from playwright.async_api import async_playwright, Browser
from app.config import Config


class PlaywrightUtils:
    def __init__(self):
        self.playwright_instance = None
        self.browser: Browser = None

    async def start(self):
        self.playwright_instance = await async_playwright().start()
        self.browser = await self.playwright_instance.chromium.launch(headless=Config.HEADLESS)

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright_instance:
            await self.playwright_instance.stop()
        self.browser = None
        self.playwright_instance = None

    async def new_context(self, storage_state=None):
        return await self.browser.new_context(storage_state=storage_state)

    async def new_page(self, context):
        return await context.new_page()

    async def get_storage_state(self, context):
        return await context.storage_state()

    async def load_storage_state(self, storage_state):
        return await self.browser.new_context(storage_state=storage_state)
