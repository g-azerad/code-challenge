from app.repositories.postgresql_db import PostgresRepo
from app.utils.playwright_utils import PlaywrightUtils
from sqlalchemy.orm import Session
from typing import Dict, Any
import traceback
import uuid
from app.model.models import CartStatus
from fastapi import HTTPException,status
from urllib.parse import urlparse
from fastapi import HTTPException
from app.handlers.handler_factory import HandlerFactory

class AddCartService:
    def __init__(
        self,
        psql_repo: PostgresRepo,
        playwright_utils: PlaywrightUtils,
        handler_factory: HandlerFactory
    ):
        self.psql_repo = psql_repo
        self.playwright_utils = playwright_utils
        self.handler_factory = handler_factory

    async def add_to_cart(
        self,
        psql_session: Session,
        cart_id: uuid,
        product_url: str,
        product_variant: str,
        quantity: int,
    ) -> Dict[str, Any]:
        try:
            cart = await self.psql_repo.get_cart_by_id(psql_session, cart_id)

            cart_products = await self.psql_repo.get_products_by_cart_id(psql_session, cart_id)
            print(cart_products)
            if cart_products:
                exst_prod_url = cart_products[0].product_url
                exst_domain = urlparse(exst_prod_url).netloc
                incoming_domain = urlparse(product_url).netloc
                
                if exst_domain != incoming_domain:
                    raise HTTPException(status_code=400, detail=f"Added product in {incoming_domain} but cart only accepts {exst_domain}")
            
            # Get existing product if url matches                
            exst_quantity = None
            updated_quantity = None
            exst_id = None

            for product in cart_products:
                if product.product_url == product_url:
                    exst_quantity = product.quantity
                    updated_quantity = quantity + exst_quantity
                    exst_id = product.id
            
            # Create a handler based on the website
            handler = self.handler_factory.get_bot_handler(website_url=product_url)            
            async with await self.playwright_utils.new_context(storage_state=cart.session_storage) as context:
                async with await self.playwright_utils.new_page(context) as page:
                    price, msrp, cart_details = await handler.add_product(page=page, quantity=quantity, exst_quantity=exst_quantity or None, product_variant=product_variant, product_url=product_url)
                    storage_state = await self.playwright_utils.get_storage_state(context)
                    print(f'save in cart: {cart_id} - {product_url}')
                    product_id = await self.psql_repo.save_product(psql_session, cart_id, product_url, product_variant, updated_quantity or quantity, price, msrp, storage_state, exst_id or None)
                    psql_session.commit()
                    print(f'Confirmed')
                    
                    return {
                        "product_id": product_id,
                        "cart_details": cart_details
                    }
        except HTTPException as e:
            psql_session.rollback()
            raise e
        except Exception as e:
            psql_session.rollback()
            print(f"Exception add_to_cart {str(e)}", traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to add product")