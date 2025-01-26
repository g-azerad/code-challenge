import os
from playwright.async_api import async_playwright, Browser
from app.config import Config


class PlaywrightUtils:
    def __init__(self):
        self.playwright_instance = None
        self.browser: Browser = None

    async def start(self):
        self.playwright_instance = await async_playwright().start()
        if os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None:
            # self.browser = await self.playwright_instance.chromium.launch(headless=Config.HEADLESS, args=["--single-process"])
            self.browser = await self.playwright_instance.chromium.launch(
                headless=True, downloads_path="/tmp",
                args=[
                    '--autoplay-policy=user-gesture-required',
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-breakpad',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-update',
                    '--disable-default-apps',
                    '--disable-dev-shm-usage',
                    '--disable-domain-reliability',
                    '--disable-extensions',
                    '--disable-features=AudioServiceOutOfProcess',
                    '--disable-hang-monitor',
                    '--disable-ipc-flooding-protection',
                    '--disable-notifications',
                    '--disable-offer-store-unmasked-wallet-cards',
                    '--disable-popup-blocking',
                    '--disable-print-preview',
                    '--disable-prompt-on-repost',
                    '--disable-renderer-backgrounding',
                    '--disable-setuid-sandbox',
                    '--disable-speech-api',
                    '--disable-sync',
                    '--disk-cache-size=33554432',
                    '--hide-scrollbars',
                    '--ignore-gpu-blacklist',
                    '--metrics-recording-only',
                    '--mute-audio',
                    '--no-default-browser-check',
                    '--no-first-run',
                    '--no-pings',
                    '--no-sandbox',
                    '--no-zygote',
                    '--password-store=basic',
                    '--use-gl=swiftshader',
                    '--use-mock-keychain',
                    '--single-process'])
        else:
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
