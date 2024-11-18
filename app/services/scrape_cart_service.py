from app.repositories.postgresql_db import PostgresRepo
from app.utils.playwright_utils import PlaywrightUtils
from app.model.models import CartStatus
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
import traceback
from fastapi import HTTPException, status
from app.handlers.handler_factory import HandlerFactory

class ScrapeCartService:
    def __init__(
        self,
        psql_repo: PostgresRepo,
        playwright_utils: PlaywrightUtils,
        handler_factory: HandlerFactory
    ):
        self.psql_repo = psql_repo
        self.playwright_utils = playwright_utils
        self.handler_factory = handler_factory

    async def scrape_cart(
        self, psql_session: Session, cart_id: uuid.UUID
    ) -> Dict[str, Any]:
        try:

            cart = await self.psql_repo.get_cart_by_id(psql_session, cart_id)

            products = await self.psql_repo.get_products_by_cart_id(psql_session, cart_id)
            if not products:
                raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Cart is empty!")

            product_url = products[0].product_url
            
            handler = self.handler_factory.get_bot_handler(website_url=product_url)
            async with await self.playwright_utils.new_context(storage_state=cart.session_storage) as context:
                async with await self.playwright_utils.new_page(context) as page:
                    return await handler.fetch_cart_details(page=page, product_url=product_url)
            
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Exception scrape_cart {str(e)}", traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to fetch cart details")
