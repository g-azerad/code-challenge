from app.model.checkout_options import CheckoutOptionsV2
from app.repositories.postgresql_db import PostgresRepo
from app.utils.playwright_utils import PlaywrightUtils
from typing import Dict, Any
from sqlalchemy.orm import Session
import uuid
from fastapi import HTTPException, status
from app.model.models import CartStatus
import traceback
from app.handlers.handler_factory import HandlerFactory



class CheckoutService:
    def __init__(
        self,
        psql_repo: PostgresRepo,
        playwright_utils: PlaywrightUtils,
        handler_factory: HandlerFactory
    ):
        self.psql_repo = psql_repo
        self.playwright_utils = playwright_utils
        self.handler_factory = handler_factory

    async def get_checkout_options(self, session: Session, cart_id: uuid.UUID) -> Dict[str, Any]:
        try:
            cart = await self.psql_repo.get_cart_by_id(session, cart_id)

            products = await self.psql_repo.get_products_by_cart_id(session, cart_id)
            if not products:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart is empty")

            product_url = products[0].product_url
            handler = self.handler_factory.get_bot_handler(website_url=product_url)

            async with await self.playwright_utils.new_context(storage_state=cart.session_storage) as context:
                async with await self.playwright_utils.new_page(context) as page:
                    details = await handler.get_checkout_options(page=page)
                    return details

        except HTTPException as e:
            session.rollback()
            raise e

    async def get_checkout_options_v2(self, session: Session, cart_id: uuid.UUID) -> CheckoutOptionsV2:
        try:
            cart = await self.psql_repo.get_cart_by_id(session, cart_id)

            products = await self.psql_repo.get_products_by_cart_id(session, cart_id)
            if not products:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart is empty")

            product_url = products[0].product_url
            handler = self.handler_factory.get_bot_handler(website_url=product_url)

            async with await self.playwright_utils.new_context(storage_state=cart.session_storage) as context:
                async with await self.playwright_utils.new_page(context) as page:
                    details = await handler.get_checkout_options_v2(page=page)
                    return details

        except HTTPException as e:
            session.rollback()
            raise e

    async def submit_order(self, session: Session, cart_id: uuid.UUID, user_info: Dict[str, Any]) -> Dict[str, Any]:
        try:
            cart = await self.psql_repo.get_cart_by_id(session, cart_id)

            products = await self.psql_repo.get_products_by_cart_id(session, cart_id)
            if not products:
                raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Cart is empty!")

            product_url = products[0].product_url
            handler = self.handler_factory.get_bot_handler(website_url=product_url)
            
            async with await self.playwright_utils.new_context(storage_state=cart.session_storage) as context:
                async with await self.playwright_utils.new_page(context) as page:
                    details = await handler.submit_order(page=page, user_info=user_info)
                    order_id = await self.psql_repo.save_order(
                        session,
                        cart,
                        details.get("order_type"),
                        details.get("payment_type"),
                        details.get("pickup_time"),
                    )
                    session.commit()
                    return {"order_id":order_id}
            
        except HTTPException as e:
            session.rollback()
            raise e
        except Exception as e:
            session.rollback()
            print(f"Exception submit_order {str(e)}", traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to submit order")

    async def submit_order_v2(self, session: Session, cart_id: uuid.UUID, checkout_options: CheckoutOptionsV2) -> Dict[str, Any]:
        try:
            cart = await self.psql_repo.get_cart_by_id(session, cart_id)

            products = await self.psql_repo.get_products_by_cart_id(session, cart_id)
            if not products:
                raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Cart is empty!")

            product_url = products[0].product_url
            handler = self.handler_factory.get_bot_handler(website_url=product_url)

            async with await self.playwright_utils.new_context(storage_state=cart.session_storage) as context:
                async with await self.playwright_utils.new_page(context) as page:
                    details = await handler.submit_order_v2(page=page, checkout_options=checkout_options)
                    order_id = await self.psql_repo.save_order(
                        session,
                        cart,
                        details.get("order_type"),
                        details.get("payment_type"),
                        details.get("pickup_time"),
                    )
                    session.commit()
                    return {"order_id": order_id}

        except HTTPException as e:
            session.rollback()
            raise e
        except Exception as e:
            session.rollback()
            print(f"Exception submit_order {str(e)}", traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to submit order")
