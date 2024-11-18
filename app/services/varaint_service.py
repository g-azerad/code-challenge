from app.repositories.postgresql_db import PostgresRepo
from app.utils.playwright_utils import PlaywrightUtils
from sqlalchemy.orm import Session
from typing import Dict, Any
import traceback
import uuid
from playwright.async_api import Page
from fastapi import HTTPException
from fastapi import APIRouter, Form, Depends, HTTPException, status
from app.handlers.handler_factory import HandlerFactory

class VariantService:
    def __init__(
        self,
        playwright_utils: PlaywrightUtils,
        handler_factory: HandlerFactory
    ):
        self.playwright_utils = playwright_utils
        self.handler_factory = handler_factory

    
    async def product_variations(self,product_url: str):
        handler = self.handler_factory.get_bot_handler(website_url=product_url)
        async with await self.playwright_utils.new_context() as context:
            async with await self.playwright_utils.new_page(context) as page:
                variant_data = await handler.get_variations(page=page, product_url=product_url)
                return variant_data 
