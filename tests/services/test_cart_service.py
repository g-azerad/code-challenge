import pytest
from unittest.mock import AsyncMock
from app.services.add_cart_service import AddCartService


@pytest.fixture
def mock_redis_repo():
    return AsyncMock()


@pytest.fixture
def mock_playwright_utils():
    return AsyncMock()

@pytest.fixture
def mock_handler_factory():
    return AsyncMock()

@pytest.fixture
def cart_service(mock_redis_repo, mock_playwright_utils, mock_handler_factory):
    return AddCartService(mock_redis_repo, mock_playwright_utils, mock_handler_factory)


@pytest.mark.asyncio
async def test_add_to_cart_success(cart_service):
    product_url = "http://example.com/product"
    cm_id = "test_cm_id"
    product_variant = "variant_123"
    quantity = 1

    mock_context = AsyncMock()
    mock_page = AsyncMock()
    cart_service.playwright_utils.new_context.return_value.__aenter__.return_value = (
        mock_context
    )
    cart_service.playwright_utils.new_page.return_value.__aenter__.return_value = (
        mock_page
    )

    cart_service._setup_response_interception = AsyncMock(return_value={})
    cart_service._perform_add_to_cart = AsyncMock(return_value={"success": True})
    cart_service._save_session_data = AsyncMock()

    result = await cart_service.add_to_cart(product_url, cm_id, product_variant, quantity)

    assert result["status"] == "success"
    assert "session_id" in result
    cart_service._perform_add_to_cart.assert_called_once()
    cart_service._save_session_data.assert_called_once()


@pytest.mark.asyncio
async def test_add_to_cart_failure(cart_service):
    product_url = "http://example.com/product"
    cm_id = "test_cm_id"
    product_variant = "variant_123"
    quantity = 20

    mock_context = AsyncMock()
    mock_page = AsyncMock()
    cart_service.playwright_utils.new_context.return_value.__aenter__.return_value = mock_context
    cart_service.playwright_utils.new_page.return_value.__aenter__.return_value = mock_page

    cart_service._perform_add_to_cart = AsyncMock(return_value={"success": False, "error": "max quantity 10"})
    cart_service._create_error_response = AsyncMock(return_value={"status": "error", "message": "max quantity 10"})

    result = await cart_service.add_to_cart(product_url, cm_id, product_variant, quantity)

    assert result["status"] == "error"
    assert result["message"] == "max quantity 10"
