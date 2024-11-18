from app.repositories.postgresql_db import PostgresRepo
from app.utils.playwright_utils import PlaywrightUtils
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
import traceback
from fastapi import HTTPException, status
from app.model.models import CartStatus
from app.handlers.handler_factory import HandlerFactory
from sqlalchemy.ext.asyncio import AsyncSession

class DeleteProductService:
    def __init__(
        self,
        psql_repo: PostgresRepo,
        playwright_utils: PlaywrightUtils,
        handler_factory: HandlerFactory
    ):
        self.psql_repo = psql_repo
        self.playwright_utils = playwright_utils
        self.handler_factory = handler_factory

    async def delete_product(
        self, psql_session: Session, cart_id: uuid.UUID, product_id: uuid.UUID
    ) -> Dict[str, Any]:
        try:

            cart = await self.psql_repo.get_cart_by_id(psql_session, cart_id)

            # Fetch product by cart_id and product_id
            product = await self.psql_repo.get_product_by_cart_and_id(psql_session, cart_id, product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} not found in Cart {cart_id}")

            # product_url = product.product_url
            handler = self.handler_factory.get_bot_handler(website_url=product.product_url)

            # Use Playwright to open the cart and remove the item
            async with await self.playwright_utils.new_context(storage_state=cart.session_storage) as context:
                async with await self.playwright_utils.new_page(context) as page:
                    await handler.delete_item_product(page=page, product_id=product_id, session=psql_session)
                    storage_state = await self.playwright_utils.get_storage_state(context)

            # Now delete the product from the database
            await self.psql_repo.delete_product(psql_session, product_id)
            await self.psql_repo.save_cart(psql_session, cart_id=cart_id, session_storage=storage_state)
            # Verify the product is deleted
            product_after_deletion = await self.psql_repo.get_product_by_cart_and_id(psql_session, cart_id, product_id)
            if product_after_deletion:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete product from the database.")

            return {"message": "Product successfully deleted from cart."}
        
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Exception delete_product {str(e)}", traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")


