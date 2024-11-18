from fastapi import HTTPException, status
from app.model.models import Cart, Product, Order, CartStatus
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import uuid
from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
class PostgresRepo:
    def __init__(self, postgres_url: str):
        self.engine = create_engine(postgres_url)

    def create_session(self):
        return Session(self.engine)

    def close_session(self, session):
        return session.close()

    async def create_cart(self, session: Session, session_id: str):
        cart = (session.query(Cart)
                .filter(Cart.session_id == session_id)
                .filter(Cart.status == CartStatus.active)
                .first())
        if cart:
            cart.status = CartStatus.inactive

        new_cart = Cart(id = uuid.uuid4(), session_id = session_id, status = CartStatus.active)
        session.add(new_cart)
        session.commit()
        return new_cart.id


    async def save_cart(self, session: Session, session_id: str, cart_id: Optional[str] = None, session_storage : Optional[dict] = None):
        # Generate a new cart_id if not provided
        if cart_id is None:
            cart_id = uuid.uuid4()  # Create a new UUID

        # Fetch the existing cart by cart_id
        cart = session.get(Cart, cart_id)

        if cart:
            # Update the existing cart's session_storage
            cart.session_storage = session_storage
        else:
            # If the cart does not exist, create a new one
            cart = Cart(id=cart_id, session_id = session_id, status = CartStatus.active, session_storage=session_storage)
            session.add(cart)

        # Commit changes to the database
        session.commit()  # Ensure any changes are committed
        return cart.id

    async def get_cart_by_id(self, session: Session, cart_id: uuid):
        cart = session.query(Cart).filter_by(id=cart_id).first()
        if cart is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cart ID {cart_id} not found")
        if cart.status != CartStatus.active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cart ID {cart_id} is {cart.status.value}")
        return cart

    async def delete_cart(self, session: Session, cart_id: uuid):
        session.query(Product).filter_by(cart_id=cart_id).delete()
        session.query(Order).filter_by(cart_id=cart_id).delete()
        session.query(Cart).filter_by(id=cart_id).delete()
        return cart_id

    async def save_product(
        self,
        session: Session,
        cart_id: uuid.UUID,
        product_url: str,
        product_variant: str,
        quantity: int,
        price: float,
        msrp: float,
        session_storage: dict[str, any],
        id: uuid.UUID = None,
    ):
        cart = session.query(Cart).filter_by(id=cart_id).one_or_none()
        if cart:
            # Use merge to handle insert or update based on primary key
            product = Product(
                id=id or uuid.uuid4(),
                cart_id=cart_id,
                product_url=product_url,
                product_variant=product_variant,
                quantity=quantity,
                price=price,
                msrp=msrp
            )
            session.merge(product)

            # Update the cart's session storage
            session.query(Cart).filter_by(id=cart_id).update({'session_storage': session_storage})
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cart ID {cart_id} not found")
        
        return product.id

    async def get_product_by_id(self, session: Session, product_id: uuid):
        product = session.query(Product).filter_by(id=product_id).first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product ID {product_id} not found")
        return product

    async def get_products_by_cart_id(self, session: Session, cart_id: uuid.UUID):
        products = session.query(Product).filter_by(cart_id=cart_id).all()
        return products

    async def get_product_by_cart_and_id(self, session: Session, cart_id: uuid.UUID, product_id: uuid.UUID):
        return session.query(Product).filter_by(cart_id=cart_id, id=product_id).first()

    async def delete_product(self, session: Session, product_id: uuid.UUID):
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} not found")
            session.delete(product)
            session.commit()
            return {"message": f"Product {product_id} deleted"}
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting product: {str(e)}")
        finally:
            session.close()

    async def save_order(selfself, session: Session, cart: Cart, order_type: str, payment_type: str, pickup_time: str):
        order = Order(
            id=uuid.uuid4(), cart_id = cart.id, order_type = order_type, payment_type = payment_type, pickup_time = pickup_time
        )
        session.add(order)
        cart.status = CartStatus.ordered
        return order.id

    async def get_order_by_id(self, session: Session, order_id: uuid):
        order = session.query(Order).filter_by(id=order_id).first()
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order ID {order_id} not found")
        print(order.__dict__)
        return order

    async def delete_order(self, session: Session, order_id: uuid):
        session.query(Order).filter_by(id=order_id).delete()
        return order_id
