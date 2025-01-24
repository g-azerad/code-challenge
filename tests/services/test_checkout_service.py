import pytest
from unittest.mock import AsyncMock
from app.services.checkout_service import CheckoutService


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
def checkout_service(mock_redis_repo, mock_playwright_utils, mock_handler_factory):
    return CheckoutService(mock_redis_repo, mock_playwright_utils, mock_handler_factory)


@pytest.mark.asyncio
async def test_proceed_to_checkout_success(checkout_service):
    session_id = "test-session-id"
    user_info = {
        "first_name": "John",
        "last_name": "Doe",
        "mobile_phone": "1234567890",
        "birthdate": "01/01/1990",
        "email": "john.doe@example.com",
        "state": "CA",
        "promo_code": None,
        "pickup_option": "store",
        "quantity": 1,
        "medical_card_number": None,
        "medical_card_expiration": None,
        "medical_card_state": None,
    }

    checkout_service._load_session = AsyncMock(return_value=AsyncMock())
    checkout_service._load_product_details = AsyncMock(
        return_value={"product_url": "http://example.com/product"}
    )
    checkout_service._perform_checkout = AsyncMock(return_value={"success": True})
    checkout_service._save_session_data = AsyncMock()
    checkout_service._create_checkout_success_response = AsyncMock(
        return_value={"status": "success"}
    )

    result = await checkout_service.proceed_to_checkout(session_id, user_info)

    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_submit_order_success(checkout_service):
    session_id = "test-session-id"

    checkout_service._load_session = AsyncMock(return_value=AsyncMock())
    checkout_service._load_product_details = AsyncMock(
        return_value={"product_name": "Test Product", "cm_id": "123"}
    )
    checkout_service._load_submit_form = AsyncMock(return_value={})
    checkout_service._submit_order = AsyncMock(
        return_value={
            "success": True,
            "pickup_time": "10:00 AM",
            "subtotal": r"\$10",
            "taxes": r"\$1",
            "order_total": r"\$11",
        }
    )
    checkout_service._save_session_state = AsyncMock()
    checkout_service._create_order_success_response = AsyncMock(
        return_value={"status": "success", "message": "Order submitted successfully!"}
    )

    result = await checkout_service.submit_order(session_id)

    assert result["status"] == "success"
    assert result["message"] == "Order submitted successfully!"
