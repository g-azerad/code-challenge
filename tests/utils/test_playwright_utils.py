import pytest
from unittest.mock import Mock, patch, AsyncMock
from playwright.async_api import async_playwright, Browser
from app.utils.playwright_utils import PlaywrightUtils
import sys


@pytest.mark.asyncio
async def test_start_and_stop():
    utils = PlaywrightUtils()
    await utils.start()
    assert utils.playwright_instance is not None
    assert utils.browser is not None
    await utils.stop()
    if sys.platform == 'win32':
        assert utils.browser is None
    else:
        assert not utils.browser.is_connected()


@pytest.mark.asyncio
async def test_new_context():
    utils = PlaywrightUtils()
    await utils.start()
    context = await utils.new_context()
    assert context is not None
    await utils.stop()


@pytest.mark.asyncio
async def test_new_page():
    utils = PlaywrightUtils()
    await utils.start()
    context = await utils.new_context()
    page = await utils.new_page(context)
    assert page is not None
    await utils.stop()


@pytest.mark.asyncio
async def test_save_storage_state():
    utils = PlaywrightUtils()
    await utils.start()
    context = await utils.new_context()
    storage_state = await utils.save_storage_state(context)
    assert storage_state is not None
    await utils.stop()


@pytest.mark.asyncio
async def test_load_storage_state():
    utils = PlaywrightUtils()
    await utils.start()
    context = await utils.new_context()
    storage_state = await utils.save_storage_state(context)
    loaded_context = await utils.load_storage_state(storage_state)
    assert loaded_context is not None
    await utils.stop()