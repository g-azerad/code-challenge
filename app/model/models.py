from typing import List
from sqlalchemy import Boolean, Column, ForeignKey, String, Integer, Float, JSON, Date, Enum
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum


class Base(DeclarativeBase):
    pass

class CartStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    ordered = "ordered"
    deleted = "deleted"

class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    session_id: Mapped[str] = mapped_column(String)
    status = Column('status', Enum(CartStatus, create_type=False))
    session_storage: Mapped[JSON] = mapped_column(JSON)
    products: Mapped[List["Product"]] = relationship()

class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    cart_id = mapped_column(UUID, ForeignKey("carts.id"))
    product_url: Mapped[str] = mapped_column(String())
    product_variant: Mapped[str] = mapped_column(String())
    quantity: Mapped[int] = mapped_column(Integer())
    price: Mapped[float] = mapped_column(Float(3))
    msrp: Mapped[float] = mapped_column(Float(3))
    cart: Mapped["Cart"] = relationship("Cart")

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    cart_id = mapped_column(UUID, ForeignKey("carts.id"))
    order_type: Mapped[str] = mapped_column(String())       # Pickup, Drive-thru, pick-up, etc
    payment_type: Mapped[str] = mapped_column(String())     # Cash, Credit card, Debit card, etc
    pickup_time: Mapped[str] = mapped_column(String())
    cart: Mapped["Cart"] = relationship("Cart")