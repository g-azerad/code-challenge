from fastapi import APIRouter, Form, Depends, HTTPException, status, Query
from .validations import SubmitOrderForm
from app.model.checkout_options import CheckoutOptionsV2
from app.services.varaint_service import VariantService
from app.services.add_cart_service import AddCartService
from app.services.scrape_cart_service import ScrapeCartService
from app.services.delete_product_service import DeleteProductService
from app.services.checkout_service import CheckoutService
from app.repositories.postgresql_db import PostgresRepo
from app.dependencies import (
    get_varaint_service,
    get_add_cart_service,
    get_scrape_cart_service,
    get_delete_product_service,
    get_checkout_service,
    get_postgres_repo,
)
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/carts", status_code=status.HTTP_201_CREATED)
async def create_cart(
        session_id: str,
        psql: PostgresRepo = Depends(get_postgres_repo)
):
    session = psql.create_session()
    cart_id = await psql.create_cart(session, session_id)
    session.commit()
    session.close()
    return {"cart_id":cart_id}


@router.get("/carts/{cart_id}", status_code=status.HTTP_200_OK)
async def get_cart(cart_id: str, psql: PostgresRepo = Depends(get_postgres_repo)):
    session = psql.create_session()
    cart = await psql.get_cart_by_id(session, cart_id)
    session.close()
    return cart


@router.delete("/carts/{cart_id}", status_code=status.HTTP_200_OK)
async def delete_cart(cart_id: str, psql: PostgresRepo = Depends(get_postgres_repo)):
    session = psql.create_session()
    cart = await psql.delete_cart(session, cart_id)
    session.commit()
    session.close()
    return cart


@router.get("/variations", status_code=status.HTTP_200_OK)
async def variations(
    product_url: str = Query(None),
    variant_service: VariantService = Depends(get_varaint_service),
):
    if not product_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="product_url is required"
        )
    response = await variant_service.product_variations(product_url)
    return response

@router.post("/carts/{cart_id}/add-product", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    cart_id: str,
    product_url: str = Form(...),
    product_variant: str = Form(None),
    quantity: int = Form(1),
    cart_service: AddCartService = Depends(get_add_cart_service),
    psql: PostgresRepo = Depends(get_postgres_repo)
):
    session = psql.create_session()
    try:
        cart_uuid = uuid.UUID(cart_id)
        response = await cart_service.add_to_cart(session, cart_uuid, product_url, product_variant, quantity)
        return response
    finally:
        psql.close_session(session)


@router.get("/products/{product_id}", status_code=status.HTTP_200_OK)
async def get_product(product_id: str, psql: PostgresRepo = Depends(get_postgres_repo)):
    session = psql.create_session()
    product = await psql.get_product_by_id(session, product_id)
    return product


@router.delete("/carts/{cart_id}/products/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(cart_id: str, product_id: str, service: DeleteProductService = Depends(get_delete_product_service), psql: PostgresRepo = Depends(get_postgres_repo)):
    session = psql.create_session()
    product = await service.delete_product(session, cart_id, product_id)
    session.commit()
    session.close()
    return product



@router.get("/orders/{order_id}", status_code=status.HTTP_200_OK)
async def get_order(order_id: str, psql: PostgresRepo = Depends(get_postgres_repo)):
    session = psql.create_session()
    order = await psql.get_order_by_id(session, order_id)
    session.close()
    return order


@router.delete("/orders/{order_id}", status_code=status.HTTP_200_OK)
async def delete_order(order_id: str, psql: PostgresRepo = Depends(get_postgres_repo)):
    session = psql.create_session()
    order = await psql.delete_order(session, order_id)
    session.commit()
    session.close()
    return order


@router.get("/carts/{cart_id}/verify", status_code=status.HTTP_200_OK)
async def get_cart_data(
    cart_id: str,
    service: ScrapeCartService = Depends(get_scrape_cart_service),
    psql: PostgresRepo = Depends(get_postgres_repo)
):
    session = psql.create_session()
    try:
        cart_uuid = uuid.UUID(cart_id)
        session.expire_all()
        response = await service.scrape_cart(session, cart_uuid)
        return response
    finally:
        psql.close_session(session)


@router.post("/carts/{cart_id}/proceed-checkout", status_code=status.HTTP_200_OK)
async def proceed_to_checkout(
    cart_id: str,
    checkout_service: CheckoutService = Depends(get_checkout_service),
    psql: PostgresRepo = Depends(get_postgres_repo)
):
    session = psql.create_session()
    try:
        cart_uuid = uuid.UUID(cart_id)
        response = await checkout_service.proceed_to_checkout(session, cart_uuid)
        return response
    finally:
        psql.close_session(session)


@router.get("/carts/{cart_id}/checkout-options", status_code=status.HTTP_200_OK)
async def user_selectable_checkout(
    cart_id: str,
    checkout_service: CheckoutService = Depends(get_checkout_service),
    psql: PostgresRepo = Depends(get_postgres_repo)
):
    session = psql.create_session()
    try:
        cart_uuid = uuid.UUID(cart_id)
        response = await checkout_service.get_checkout_options(session, cart_uuid)
        return response
    finally:
        psql.close_session(session)


@router.post("/carts/{cart_id}/submit-order", status_code=status.HTTP_200_OK)
async def submit_order(
    cart_id: str,
    form_data: SubmitOrderForm = Depends(SubmitOrderForm.as_form),
    checkout_service: CheckoutService = Depends(get_checkout_service),
    psql: PostgresRepo = Depends(get_postgres_repo)
):
    session = psql.create_session()
    try:
        cart_uuid = uuid.UUID(cart_id)
        user_info = form_data.model_dump()
        user_info["medical_card_expiration"] = (
            datetime.strptime(user_info["medical_card_expiration"], "%m/%d/%Y").date()
            if user_info["medical_card_expiration"]
            else None
        )
        response = await checkout_service.submit_order(session, cart_uuid, user_info)
        return response
    finally:
        psql.close_session(session)

@router.get("/carts/{cart_id}/checkout-options-v2", status_code=status.HTTP_200_OK)
async def user_selectable_checkout_v2(
    cart_id: str,
    checkout_service: CheckoutService = Depends(get_checkout_service),
    psql: PostgresRepo = Depends(get_postgres_repo)
):
    session = psql.create_session()
    try:
        cart_uuid = uuid.UUID(cart_id)
        response = await checkout_service.get_checkout_options_v2(session, cart_uuid)
        return response.model_dump(exclude_none=True)
    finally:
        psql.close_session(session)

@router.post("/carts/{cart_id}/submit-order-v2", status_code=status.HTTP_200_OK)
async def submit_order_v2(
    cart_id: str,
    checkout_options: CheckoutOptionsV2,
    checkout_service: CheckoutService = Depends(get_checkout_service),
    psql: PostgresRepo = Depends(get_postgres_repo)
):
    session = psql.create_session()
    try:
        cart_uuid = uuid.UUID(cart_id)
        response = await checkout_service.submit_order_v2(session, cart_uuid, checkout_options)
        return response
    finally:
        psql.close_session(session)
