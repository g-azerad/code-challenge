import random
from abc import ABC, abstractmethod
from app.model.models import Product
from app.model.checkout_options import *
from app.services.selectors_service import SelectorsService
from fastapi import HTTPException, status
from playwright._impl._errors import TimeoutError, Error
from playwright.async_api import Page
from sqlalchemy.orm import Session
from typing import Dict, Optional, Any
import traceback
import uuid
import asyncio


class BaseHandlerRefactor(ABC):

    def __init__(self):
        self.selectors = SelectorsService.get_selectors(self.bot_name)["selectors"]

    async def raise_http_exception(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        exception: Exception = None,
        context: str = "",
        variants: list = None,
    ):
        if exception:
            print(
                f"Exception {context}: {exception}\nTraceback: {traceback.format_exc()}"
            )

        detail = {"status": "error", "message": message}
        if variants is not None:  # Add variants to the detail if provided
            detail["variants"] = variants
        raise HTTPException(
            status_code=status_code,detail=detail
        )

    async def navigate_to_url(self, page: Page, product_url: str):
        """
        Common method to navigate to the product page and wait for the load state.
        """
        await page.goto(product_url)
        await page.wait_for_load_state("load")

    async def _handle_extra_modal(self, page: Page, modal_selector: str, button_selector: str, timeout: Optional[int] = 1000):
        try:
            modal_container = page.locator(modal_selector)
            await modal_container.wait_for(state="visible", timeout=timeout)
            button = modal_container.locator(button_selector)
            await button.click()
        except (TimeoutError, Error):
            pass

    async def _handle_imp_modal(self, page: Page, modal_selector: str, exc_message: str, timeout: Optional[int] = 5000, status_code: status = status.HTTP_400_BAD_REQUEST):
        try:
            await page.locator(modal_selector).wait_for(state="visible", timeout=timeout)
            await self.raise_http_exception(exc_message, status_code=status_code)
        except TimeoutError:
            pass

    async def _handle_error_notification(self, page: Page, notification_selector: str, exc_message: str, timeout: Optional[int] = 1000):
        """
        Default method to check if there is a error notification.
        """
        try:
            notification = page.locator(notification_selector)
            if await notification.is_visible(timeout=2000):
                notification_text = await notification.inner_text()
                await self.raise_http_exception(
                    exc_message.format(notification_text),
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        except TimeoutError:
            pass

    async def _check_out_of_stock(self, page: Page, out_of_stock_selector: str, inner_text: Optional[str] = None, timeout: Optional[int] = 2000):
        """
        Checks if a product is out of stock based on the provided selector.
        """
        try:
            out_of_stock_element = await page.wait_for_selector(out_of_stock_selector, timeout=timeout)

            if inner_text:
                message_text = await out_of_stock_element.inner_text()
                if inner_text in message_text:
                    await self.raise_http_exception("Product is out of stock", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
            else:
                await self.raise_http_exception("Product is out of stock", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except (TimeoutError, Error):
            print("Product is available.")

    async def _handle_product_variant(self, page: Page, product_variant_selector: Dict[str, str], provided_variant: Optional[str] = None):
        """
        Handles the variant selection process for products. Works across different websites.
        - If no variants are available, proceed with the process.
        - If one variant is available, select it automatically.
        - If multiple variants are available, check the provided variant and select it.
        Returns the selected variant and its price or raises an exception if the variant is incorrect.
        """
        available_variants = []
        variant_elements = await page.query_selector_all(product_variant_selector['variant_selector'])

        # Scenario 1: No variants found
        if not variant_elements:
            return {"message": "No variants available, proceeding with the product."}

        # Collect all available variants
        for element in variant_elements:
            variant_name_element = await element.query_selector(product_variant_selector['variant_name_selector'])
            price_selector = product_variant_selector.get('variant_price_selector')

            if isinstance(price_selector, str):
                price_element = await element.query_selector(price_selector)
            else:
                price_element = price_selector

            variant_name = await variant_name_element.inner_text() if variant_name_element else None
            price = await price_element.inner_text() if price_element else None

            available_variants.append({"variant_name": variant_name, "price": price})


            # Scenario 2: Multiple variants available
            if provided_variant and provided_variant == variant_name:
                await element.click()
                return {"message": f"Selected variant: {provided_variant}", "price": price}

        # Scenario 3: One variant available, select it automatically
        if len(available_variants) == 1:
            await variant_elements[0].click()
            return {"message": f"Single variant found: {available_variants[0]['variant_name']}. Proceeding.", "price": available_variants[0]['price']}

        # Scenario 4: Provided variant is incorrect or not matched
        if provided_variant:
            await self.raise_http_exception(
                message="Incorrect variant provided. Please provide valide variant",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        # Scenario 5: No variant was provided but multiple are available
        await self.raise_http_exception(
            message="No variant provided. Please provide valide variant",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    async def _extract_price_and_msrp(
            self, page: Page, price_selector: str, msrp_selector: str
    ):
        """
        Extracts price and MSRP from the page using provided selectors.
        """
        # await asyncio.sleep(3)
        price_elements = await page.query_selector_all(price_selector)
        product_price = None

        for element in price_elements:
            if await element.is_visible():
                price_text = await element.inner_text()
                if "$" in price_text and price_text.strip().startswith('$'):
                    product_price = float(price_text.replace("$", "").strip())
                    break

        if product_price is None:
            await self.raise_http_exception(
                "Price extraction failed", status_code=status.HTTP_404_NOT_FOUND
            )

        product_msrp = product_price
        # Extract MSRP if available
        msrp_element = await page.query_selector(msrp_selector)
        if msrp_element and await msrp_element.is_visible():
            msrp_text = await msrp_element.inner_text()
            product_msrp = float(msrp_text.replace("$", "").strip())

        return product_price, product_msrp

    async def _select_quantity_base(
            self, page: Page, selector: str, desired_quantity: int, timeout: Optional[int] = 2000
    ):
        """
        Default method to select the quantity of the product.
        """
        try:
            quantity_elm = await page.wait_for_selector(selector.format(desired_quantity), timeout=timeout)
            await quantity_elm.click()
        except TimeoutError:
            await self.raise_http_exception(
                f"Failed to select quantity: {desired_quantity}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    async def _click_add_to_cart(self, page: Page, add_to_cart_selector: str):
        """
        Default method to click the 'Add to Cart' button.
        """
        add_to_cart_button = page.locator(add_to_cart_selector)
        await add_to_cart_button.click()

    async def _fill_user_form(self, page: Page, user_info: Dict[str, Any], selectors: Dict[str, str]):
        """
        Fills the user form with details like first name, last name, email, etc.
        """
        gov_id_button = selectors.get('gov_id_button')
        if gov_id_button:
            if await page.locator(gov_id_button).is_visible():
                await self.raise_http_exception(
                    "This dispensary requires government ID upload", 
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

        await self._fill_field(page, selectors.get('mmj_id'), str(random.randint(100000000, 999999999)))
        await self._fill_field(page, selectors['first_name'], user_info['first_name'])
        await self._fill_field(page, selectors['last_name'], user_info['last_name'])
        await self._fill_field(page, selectors['email'], user_info['email'])
        await self._fill_field(page, selectors['mobile_phone'], user_info['mobile_phone'])
        await self._fill_field(page, selectors['birthdate'], user_info['birthdate'])

    async def _fill_user_form_v2(self, page: Page, checkout_options: CheckoutOptionsV2, selectors: Dict[str, str]):
        """
        Fills the user form with details like first name, last name, email, etc.
        """
        gov_id_button = selectors.get('gov_id_button')
        if gov_id_button:
            if await page.locator(gov_id_button).is_visible():
                await self.raise_http_exception(
                    "This dispensary requires government ID upload",
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

        def _get_customer_info(value: str):
            ui_field = next(field for field in checkout_options.customer_info.fields if field.label == value)
            return ui_field.get_value()

        await self._fill_field(page, selectors.get('mmj_id'), str(random.randint(100000000, 999999999)))
        await self._fill_field(page, selectors['first_name'], _get_customer_info("firstName"))
        await self._fill_field(page, selectors['last_name'], _get_customer_info("lastName"))
        await self._fill_field(page, selectors['email'], _get_customer_info("email"))
        await self._fill_field(page, selectors['mobile_phone'], _get_customer_info("phone"))
        await self._fill_field(page, selectors['birthdate'], _get_customer_info("birthdate"))


    async def _fill_field(self, page: Page, selector: str, value: str, timeout: Optional[int] = 1000):
        """
        Fills a field given a selector and a value.
        """
        if selector:
            field = page.locator(selector)
            if await field.is_visible(timeout=timeout):
                await field.fill(value)

    async def _choose_order_type(self, page: Page, selectors: Dict[str, str], timeout: Optional[int] = 1000):
        """
        Default method to select order type (e.g., Pickup).
        """
        order_type_button = page.locator(selectors['order_type'])
        if await order_type_button.is_visible(timeout=timeout):
            await order_type_button.click()    

    async def _choose_payment_method(self, page: Page, selectors: Dict[str, str], payment_method_type: str = None, timeout: Optional[int] = 1000):
        """
        Selects the specified payment method (creditCard, cash, or debit).
        Args:
            page (Page): The Playwright page instance.
            selectors (Dict[str, str]): A dictionary of selectors, including the 'payment_method' key.
            payment_type (Optional[str]): The payment method to select ('creditCard', 'cash', or 'debit'). If None, defaults to the first available option.
            timeout (Optional[int]): Timeout for the payment method button to be visible.
        """
        try:
            # Locate the payment method section
            payment_method_save_button = page.locator(selectors['payment_method_selectors'])
            
            # Ensure the payment method section is visible
            if await payment_method_save_button.is_visible(timeout=timeout):
                print(f"Payment method button found: {payment_method_save_button}")

                # If a specific payment_type is provided, select it
                if payment_method_type:
                    # Locate the radio button based on payment_type and select it
                    radio_button = page.locator(f"//input[@name='paymentType' and @value='{payment_method_type}']").first
                    print(radio_button)
                    
                    # Check if the radio button is available and attempt to click it
                    if await radio_button.is_visible():
                        await radio_button.scroll_into_view_if_needed()
                        await radio_button.click(force=True)
                        print(f"Selected payment method: {payment_method_type}")
                    else:
                        print(f"Payment type '{payment_method_type}' is not visible or selectable.")
                else:
                    print("No specific payment method provided, default option will be used.")

                # Click the save button after selecting the payment method
                await payment_method_save_button.click()
                print("Clicked the save button.")
            else:
                print("Payment method section is not visible.")
        except TimeoutError:
            print("The operation timed out. Could not select the payment method.")


    async def _place_order(self, page: Page, submit_selectors: Dict[str, str],
                           captcha_selectors: Optional[Dict[str, str]] = None, timeout: Optional[int] = 50000):
        """
        Default method to click the 'Place Order' button.
        """
        place_order_button = page.locator(submit_selectors['place_order']).first
        if await place_order_button.is_visible():
            await place_order_button.scroll_into_view_if_needed()
            await place_order_button.click()
        else:
            await page.evaluate('window.scrollTo(0, 0);')
            await place_order_button.wait_for(state="visible")
            await place_order_button.scroll_into_view_if_needed()
            await place_order_button.click()

        if captcha_selectors:
            await self._handle_captcha(page, frame_selector=captcha_selectors["frame_selector"],
                                       modal_selector=captcha_selectors["modal_selector"])
        try:
            await page.wait_for_selector(submit_selectors.get('order_success'), timeout=timeout, state="visible")
            return
        except TimeoutError:
            await self.raise_http_exception("Order submission failed: success check failed",
                                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def _handle_captcha(self, page: Page, frame_selector: str, modal_selector: str,
                              timeout: Optional[int] = 2000):
        try:
            iframe = page.frame_locator(frame_selector).first
            captcha_modal = iframe.locator(modal_selector)
            if await captcha_modal.is_visible(timeout=timeout):
                await self.raise_http_exception("Order submission failed: captcha appeared",
                                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except TimeoutError:
            print("Captcha did not appear")
            pass

    async def get_variations(self, page: Page, product_url: str):
        await self.navigate_to_url(page, product_url)
        await self._initial_checks(page)

        await self._check_out_of_stock(page, out_of_stock_selector=self.selectors["variant"]["out_of_stock_selector"])

        product_variant_selector = {
            "dispensary_name": self.selectors["variant"].get("dispensary_name"),
            "dispensary_image_element": self.selectors["variant"].get("dispensary_image_element"),
            "product_name": self.selectors["variant"].get("product_name"),
            "image_selector": self.selectors["variant"].get("image_selector"),
            "variant_selector": self.selectors["variant"].get("variant_selector"),
            "variant_name_selector": self.selectors["variant"].get("variant_name_selector"),
            "variant_price_selector": self.selectors["variant"].get("variant_price_selector"),
        }

        dispensary_name = await page.query_selector(product_variant_selector['dispensary_name'])
        disp_name = await dispensary_name.inner_text() if dispensary_name else None

        dispensary_image_url = None
        if product_variant_selector['dispensary_image_element']:
            dispensary_image_element = await page.query_selector(product_variant_selector['dispensary_image_element'])
            if dispensary_image_element:
                dispensary_image_url = await dispensary_image_element.get_attribute("src")

        image_element = await page.query_selector(product_variant_selector['image_selector'])
        product_image_url = None
        if image_element:
            product_image_url = await image_element.get_attribute("data-src")
            if not product_image_url:
                product_image_url = await image_element.get_attribute("src")

        product_name = await page.query_selector(product_variant_selector['product_name'])
        prod_name = await product_name.inner_text() if dispensary_name else None

        base_details = {
            "dispensary_name": disp_name,
            "dispensary_image_url": dispensary_image_url,
            "product_name": prod_name,
            "product_image_url": product_image_url
        }
        variant_elements = []
        for selector in product_variant_selector['variant_selector']:
            variant_elements = await page.query_selector_all(selector)
            if variant_elements:
                break

        variants = []
        if variant_elements:
            for element in variant_elements:
                variant_name_element = await element.query_selector(product_variant_selector['variant_name_selector'])

                # Extract both price and msrp
                pricing_info = await self._extract_variation_price_and_msrp(page, element)
                price = pricing_info.get("price")
                msrp = pricing_info.get("msrp")

                # Retrieve variant name if it exists
                variant_name = await variant_name_element.inner_text() if variant_name_element else None

                # Include both price and msrp in variant details
                variant_details = {k: v for k, v in [("variant_name", variant_name), ("price", price), ("msrp", msrp)] if v is not None}
                variants.append(variant_details)
        else:
            # If no variant elements are found, fetch general price and msrp directly from the page
            pricing_info = await self._extract_variation_price_and_msrp(page, page)
            price = pricing_info.get("price")
            msrp = pricing_info.get("msrp")
            
            variant_details = {k: v for k, v in [("price", price), ("msrp", msrp)] if v is not None}
            variants.append(variant_details)

        return {
            "variations": {
                **base_details,
                "variants": variants
            }
        }



    async def add_product(self, page, product_url, quantity, exst_quantity, product_variant):
        await self.navigate_to_url(page, product_url)

        # Handle other initial checks
        await self._initial_checks(page)

        # Check non-existing product page
        await self._handle_imp_modal(
            page,
            modal_selector=self.selectors["add_to_cart"]["page_not_found"],
            exc_message="Requested product page does not exist.",
            timeout=2000,
            status_code=status.HTTP_404_NOT_FOUND
        )

        # Check out of stock
        await self._check_out_of_stock(
            page,
            out_of_stock_selector=self.selectors["add_to_cart"]["out_of_stock_selector"],
            inner_text=self.selectors["add_to_cart"].get("out_of_stock_inner_text")
        )

        product_variant_selector = {
            "variant_selector" : self.selectors["add_to_cart"]["variant_selector"],
            "variant_name_selector" : self.selectors["add_to_cart"]["variant_name_selector"],
            "variant_price_selector" : self.selectors["add_to_cart"].get("variant_price_selector"),
        }
        await self._handle_product_variant(
            page=page, 
            provided_variant=product_variant,
            product_variant_selector=product_variant_selector
        )

        # Get the product name
        product_name_element = await page.wait_for_selector(self.selectors["add_to_cart"]["prod_name"])
        prod_name = await product_name_element.inner_text()
        
        # Extract price and MSRP
        for price_selector, msrp_selector in zip(self.selectors["add_to_cart"]["price_selectors"].values(),
                                                 self.selectors["add_to_cart"]["msrp_selectors"].values()):
            if await page.is_visible(price_selector):
                price, msrp = await self._extract_price_and_msrp(
                    page,
                    price_selector=price_selector,
                    msrp_selector=msrp_selector,
                )
                break

        await self._select_quantity(page, quantity, exst_quantity)
        await self._click_add_to_cart(page, add_to_cart_selector=self.selectors["add_to_cart"]["click_add_to_cart"])
        await self._bag_check(page)

        cart_container = await page.wait_for_selector(self.selectors["cart_verification"]["wait_for_cart_container"], timeout=5000)
        await self._check_cart_empty(page, cart_container)

        # Check the dispensary name
        disp_check = await page.wait_for_selector(self.selectors["add_to_cart"]["bag_check_selector"])
        dispensary_name_element = await disp_check.query_selector(self.selectors["add_to_cart"]["dispensary_name"])
        dispensary_name = await dispensary_name_element.inner_text() if dispensary_name_element else "Unknown Dispensary"

        cart_item_containers = await self._get_cart_item_containers(page, cart_container)

        for cart_item_container in cart_item_containers:
            # Match product name
            item_name_elem = await cart_item_container.query_selector(self.selectors["add_to_cart"]["item_name"])
            product_name = await item_name_elem.inner_text() if item_name_elem else "N/A"

            if prod_name in product_name:
                # If a variant is provided, match it
                if product_variant:
                    product_variant_elem = await cart_item_container.query_selector(self.selectors["add_to_cart"]["product_variant"])
                    if product_variant_elem:
                        if await self._match_product_variant(product_variant_elem, product_variant, product_name):
                            # If variant matches, extract product details
                            cart_details = await self._extract_cart_item_details(cart_item_container, product_name, dispensary_name)
                            break
                        else:
                            await self.raise_http_exception("Variant mismatch in cart", status_code=status.HTTP_404_NOT_FOUND)
                else:
                    cart_details = await self._extract_cart_item_details(cart_item_container, product_name, dispensary_name)
                    break

        if not cart_details:
            await self.raise_http_exception(f"Product {prod_name} not found in cart", status_code=status.HTTP_404_NOT_FOUND)

        return price, msrp, cart_details

    async def _extract_cart_item_details(self, cart_item_container, product_name: str, dispensary_name: str) -> Dict[str, Any]:
        """
        Extracts and returns the details (name, price, quantity) of a product from a cart item container.
        """
        item_price_elem = await cart_item_container.query_selector(self.selectors["add_to_cart"]["item_price"])
        item_price = await item_price_elem.inner_text() if item_price_elem else 'N/A'

        item_quantity_elem = await cart_item_container.query_selector(self.selectors["add_to_cart"]["item_quantity"])
        item_quantity = await item_quantity_elem.inner_text() if item_quantity_elem else 'N/A'

        return {
            "dispensary_name": dispensary_name,
            "item_name": product_name,
            "item_price": item_price,
            "item_quantity": item_quantity
        }

    async def _match_product_variant(self, product_variant_elem, product_variant, product_name) -> bool:
        """
        Dutchie-specific logic for matching product variants.
        """
        cart_variant_text = await product_variant_elem.inner_text()
        if '$' in cart_variant_text:
            price_segment = cart_variant_text.split("$")[1]
            cart_variant_value = price_segment.split("/")[1].strip()
            return product_variant == cart_variant_value

        return product_variant in cart_variant_text

    async def fetch_cart_details(self, page, product_url):
        await self.navigate_to_url(page, product_url)
        await self._initial_checks(page)

        await self._click_on_cart(page)

        # Wait for cart items container to be visible
        cart_container = await page.wait_for_selector(self.selectors["cart_verification"]["wait_for_cart_container"], timeout=5000)

        await self._check_cart_empty(page, cart_container)

        cart_item_containers = await self._get_cart_item_containers(page, cart_container)

        cart_data = []
        for cart_item_container in cart_item_containers:
            # Extract item details
            item_name_elem = await cart_item_container.query_selector(self.selectors["cart_verification"]["item_name"])
            item_name = await item_name_elem.inner_text() if item_name_elem else 'N/A'

            item_price_elem = await cart_item_container.query_selector(self.selectors["cart_verification"]["item_price"])
            item_price = await item_price_elem.inner_text() if item_price_elem else 'N/A'

            item_quantity_elem = await cart_item_container.query_selector(self.selectors["cart_verification"]["item_quantity"])
            item_quantity = await item_quantity_elem.inner_text() if item_quantity_elem else 'N/A'

            cart_data.append({
                "item_name": item_name,
                "item_price": item_price,
                "item_quantity": item_quantity
            })

        # Fetch subtotal
        subtotal_element = await page.query_selector(self.selectors["cart_verification"]["subtotal"])
        if subtotal_element:
            subtotal_str = await subtotal_element.inner_text()
            price = subtotal_str.strip('$').strip()
        else:
            price = 'N/A'

        return {
            "cart_items": cart_data,
            "subtotal": price
        }

    async def delete_item_product(self, page, product_id: uuid.UUID, session: Session):
        product = session.query(Product).filter(Product.id == product_id).first()
        product_url = product.product_url
        await self.navigate_to_url(page, product_url)

        await self._initial_checks(page)

        product_name_element = await page.wait_for_selector(self.selectors["cart_deletion"]["prod_name"])
        prod_name = await product_name_element.inner_text()

        await self._click_on_cart(page)

        # Wait for cart items container to be visible
        cart_container = await page.wait_for_selector(self.selectors["cart_deletion"]["wait_for_cart_container"],
                                                      timeout=5000)

        await self._check_cart_empty(page, cart_container)

        await page.wait_for_selector(self.selectors["cart_deletion"]["product_name"])
        cart_items = await page.query_selector_all(self.selectors["cart_deletion"]["product_name"])

        matched_product = None
        matched_index = None

        for index, item in enumerate(cart_items):
            product_name = await item.inner_text()

            if prod_name in product_name:
                matched_product = item
                matched_index = index
                print(f"Matched product: {product_name} (Prod Name: {prod_name})")
                break

        await self._handle_cart_variants(matched_index, page, product)

        # Log success before deletion
        print(f"Proceeding to delete product: {product_name}")
        delete_buttons = await page.query_selector_all(self.selectors["cart_deletion"]["product_delete_button"])
        delete_button = delete_buttons[matched_index]
        await asyncio.sleep(2)
        await delete_button.click()
        return {"message": "Product successfully deleted from cart."}

    async def get_checkout_options(self, page: Page):
        checkout_url = SelectorsService.get_checkout_url(self._get_bot_name())
        await self.navigate_to_url(page, checkout_url)
        await self._initial_checks(page)
        
        data = await self._fetch_checkout_options(page)

        checkout_options = CheckoutOptions(
            pickup_slots=data.get("pickup_slots"),
            pickup_instructions=data.get("pickup_instructions"),
            customer_info=data.get("customer_info"),
            payment_details=data.get("payment_details"),
            state_selection=data.get("state_selection"),
            order_type_details=data.get("order_type_details"),
            selected_order_data=data.get("selected_order_data"),
            extra_fields=data.get("extra_fields"),
            medical_section_details=data.get("medical_section_details")
        )

        return checkout_options.to_dict()

    async def get_checkout_options_v2(self, page: Page):
        checkout_url = SelectorsService.get_checkout_url(self._get_bot_name())
        await self.navigate_to_url(page, checkout_url)
        await self._initial_checks(page)

        data = await self._fetch_checkout_options(page)

        order_type_str = list(data.get("order_type_details").keys())[0]
        pickup_label = data.get("order_type_details").get("pickup").get("label")
        customer_info = CustomerInfo(fields = [InputField(label = i.get("label"), selector="") for i in data.get("customer_info")])
        if data.get("state_selection"):
            state_field = InputField(label="state", type="input", selector="")
            customer_info.fields.append(state_field)
        payment_options = [field["label"] for field in data.get("payment_details")]
        order_type = SingleSelectionField(options=["pickup"], label=pickup_label, selector="")
        pickup_options = [slot["label"] for slot in data.get("pickup_slots")]

        checkout_options = CheckoutOptionsV2(
            customer_info= customer_info,
            order_type=order_type,
            payment_details=SingleSelectionField(label="payment", options=payment_options, selector=""),
            pickup_slots=SingleSelectionField(label="pickup", options=pickup_options, selector="")
        )

        return checkout_options

    async def submit_order(self, page: Page, user_info: Dict[str, Any]) -> Dict[str, Any]:
        checkout_url = SelectorsService.get_checkout_url(self._get_bot_name())
        await self.navigate_to_url(page, checkout_url)
        await self._initial_checks(page)
        await self._checkout_checks(page)

        await self._fill_user_form(page, user_info, self._get_checkout_selectors())

        order_details = await self._place_order_details(page, user_info)
        return order_details

    async def submit_order_v2(self, page: Page, checkout_options: CheckoutOptionsV2) -> Dict[str, Any]:
        checkout_url = SelectorsService.get_checkout_url(self._get_bot_name())
        await self.navigate_to_url(page, checkout_url)
        await self._initial_checks(page)
        await self._checkout_checks(page)

        await self._fill_user_form_v2(page, checkout_options, self._get_checkout_selectors())

        order_details = await self._place_order_details_v2(page, checkout_options)
        return order_details

    @abstractmethod
    def _get_bot_name(self):
        """
        Abstract method to get this bot's name
        """

    @abstractmethod
    def _get_checkout_selectors(self):
        """
        Abstract method to return all the checkout selectors
        """

    @abstractmethod
    async def _place_order_details(self, page: Page, user_info: Dict[str, Any]):
        """
        Abstract method to place an order and return the order details
        """

    @abstractmethod
    async def _place_order_details_v2(self, page: Page, checkout_options: CheckoutOptionsV2):
        """
        Abstract method to place an order and return the order details
        """

    @abstractmethod
    async def _checkout_checks(self, page):
        """
        Abstract method to extra initial checks related to the checkout process
        """

    @abstractmethod
    async def _handle_cart_variants(self, matched_product, matched_index, page: Page, product_url: str):
        """
        Abstract method to check if a product was found
        """

    @abstractmethod
    async def _click_on_cart(self, page: Page):
        """
        Abstract method to click on the cart icon to brin the cart up
        """

    @abstractmethod
    async def _initial_checks(self, page: Page):
        """
        Abstract method to perform initial checks in the page for things like user preferences, etc
        """

    @abstractmethod
    async def _bag_check(self, page: Page):
        """
        Abstract method to check the bag after a product has been added
        """

    @abstractmethod
    async def _select_quantity(self, page: Page, quantity: int, exst_quantity: Optional[int]):
        """
        Abstract method to select how many products we add to the cart
        """

    @abstractmethod
    async def _check_cart_empty(self, page: Page, cart_container: Page):
        """
        Abstract method to check if a cart is empty
        """

    @abstractmethod
    async def _get_cart_item_containers(self, page: Page, cart_container: Page):
        """
        Abstract method to obtain all the cart item containers
        """

    @abstractmethod
    async def _fetch_checkout_options(self, page: Page):
        """
        Abstract method to get all the user selectable checkout options
        """

    @abstractmethod
    async def _extract_variation_price_and_msrp(self, page, variation_element):
        """
        Abstract method to extract variation price
        """
