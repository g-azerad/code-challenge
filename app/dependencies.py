from app.services.add_cart_service import AddCartService
from app.services.checkout_service import CheckoutService
from app.services.scrape_cart_service import ScrapeCartService
from app.services.delete_product_service import DeleteProductService
from app.services.varaint_service import VariantService
from app.repositories.postgresql_db import PostgresRepo
from app.utils.playwright_utils import PlaywrightUtils
from app.handlers.handler_factory import HandlerFactory
from app.config import Config
from app.services.selectors_service import SelectorsService


def initialize_services():
    config = Config()

    # Load selectors once when app starts
    SelectorsService.load_all_selectors(directory=config.SELECTORS_PATH)

    # Initialize other blocks
    postgres_repo = PostgresRepo(config.POSTGRES_CONN)
    playwright_utils = PlaywrightUtils()
    handler_factory = HandlerFactory()

    # Service instances
    varaint_service = VariantService(playwright_utils, handler_factory)
    add_cart_service = AddCartService(postgres_repo, playwright_utils, handler_factory)
    scrape_cart_service = ScrapeCartService(postgres_repo, playwright_utils, handler_factory)
    checkout_service = CheckoutService(postgres_repo, playwright_utils, handler_factory)
    delete_product_service = DeleteProductService(postgres_repo, playwright_utils, handler_factory)

    return {
        "postgres_repo": postgres_repo,
        "playwright_utils": playwright_utils,
        "varaint_service": varaint_service,
        "add_cart_service": add_cart_service,
        "delete_product_service" : delete_product_service,
        "scrape_cart_service": scrape_cart_service,
        "checkout_service": checkout_service,
    }



services_cache = None

async def get_services():
    global services_cache
    if services_cache is None:
        services_cache = initialize_services()
    return services_cache



async def get_postgres_repo():
    return (await get_services())["postgres_repo"]

async def get_playwright_utils():
    return (await get_services())["playwright_utils"]

async def get_varaint_service():
    return (await get_services())["varaint_service"]

async def get_add_cart_service():
    return (await get_services())["add_cart_service"]

async def get_scrape_cart_service():
    return (await get_services())["scrape_cart_service"]

async def get_delete_product_service():
    return (await get_services())["delete_product_service"]

async def get_checkout_service():
    return (await get_services())["checkout_service"]