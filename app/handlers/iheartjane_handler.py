from app.handlers.base_handler import BaseHandlerRefactor
from app.services.selectors_service import SelectorsService
from playwright.async_api import Page
from playwright._impl._errors import TimeoutError
from typing import Dict, Optional, Any, List
from sqlalchemy.orm import Session
from app.model.models import Product
from app.model.checkout_options import CheckoutOptions
from fastapi import status
import random
import asyncio
import os

class IHeartJaneHandler(BaseHandlerRefactor):
    """
    iHeartJane Add Cart Handler - Handles adding products to the cart on the iHeartJane website.
    """
    def __init__(self):
        self.bot_name = "iheartjane"
        super().__init__()

    def _get_bot_name(self):
        return "iheartjane"

    def _get_checkout_selectors(self):
        return {
            'mmj_id':self.selectors["checkout"]["mmj_id_input"],
            'gov_id_button': self.selectors["checkout"]["gov_id_button"],
            'first_name': self.selectors["checkout"]["first_name_input"],
            'last_name': self.selectors["checkout"]["last_name_input"],
            'email': self.selectors["checkout"]["email_input"],
            'mobile_phone': self.selectors["checkout"]["phone_input"],
            'birthdate': self.selectors["checkout"]["birth_date_input"],
        }

    async def _place_order_details(self, page: Page, user_info: Dict[str, Any]):
        await self._click_continue(page, timeout=2000, button_index=1)

        # Select payment option (custom for iHeartJane)
        await self._select_payment_option(page)

        pickup_time_elm = page.locator(self.selectors["checkout"]["pickup_method_locator"])
        pickup_time = await pickup_time_elm.inner_text() if await pickup_time_elm.is_visible(timeout=500) else None

        # Place the order using default method
        submit_selectors = {
            'place_order': self.selectors["checkout"]["place_order"],
            'order_success': self.selectors["checkout"]["successful_message"]
        }
        captcha_selectors = {
            "frame_selector": self.selectors["checkout"]["iframe"],
            "modal_selector": self.selectors["checkout"]["is_captcha"]
        }

        # Place the order
        await self._place_order(page, submit_selectors, captcha_selectors, timeout=5000)

        # Gather order details
        order_details = {
            "order_type": "Pickup",
            "payment_type": "cash",
            "pickup_time": pickup_time or "N/A",
        }
        return order_details

    async def _initial_checks(self, page: Page):
        # Handle age restriction
        await self._handle_extra_modal(
            page,
            modal_selector=self.selectors["add_to_cart"]["age_rstr_container"],
            button_selector=self.selectors["add_to_cart"]["age_rstr_btn"],
            timeout=2000
        )

        # Handle user preferences/location modal
        await self._handle_extra_modal(
            page,
            modal_selector=self.selectors["add_to_cart"]["user_pref_container"],
            button_selector=self.selectors["add_to_cart"]["user_pref_container_dismiss_button"],
            timeout=2000
        )

        await self._check_not_available(
            page,
            not_available_selector = self.selectors["add_to_cart"]["not_available_near_you_selector"]
            )

    async def _bag_check(self, page: Page):
        # Modal check for other dispensary products in cart
        await self._handle_imp_modal(
            page,
            modal_selector=self.selectors["add_to_cart"]["clear_cart_selector"],
            exc_message="Clear the cart before adding products from a new dispensary",
            timeout=2000
        )
        
        cart_drawer = page.locator(self.selectors["add_to_cart"]["bag_check_selector"])
        flag = await cart_drawer.is_visible(timeout=2000)
        if not flag:
            await self._click_on_cart(page)

    async def _select_quantity(self, page: Page, quantity: int, exst_quantity: Optional[int]):
        """
        Custom method to select quantity for iHeartJane (using increment/decrement buttons).
        """
        if exst_quantity:
            quantity = quantity + exst_quantity
        
        quantity_selector = self.selectors["add_to_cart"]["quantity_selector"]
        current_quantity_text =await page.locator(quantity_selector).inner_text()
        current_quantity = int(current_quantity_text.split(": ")[1])

        # Use dynamic selectors for increment and decrement buttons
        increment_button = page.locator(self.selectors["add_to_cart"]["increment_button"])
        decrement_button = page.locator(self.selectors["add_to_cart"]["decrement_button"])

        if current_quantity < quantity:
            for _ in range(quantity - current_quantity):
                increment_button_disabled = await increment_button.get_attribute("disabled")
                if increment_button_disabled is not None:
                    break
                await increment_button.click()
        elif current_quantity > quantity:
            for _ in range(current_quantity - quantity):
                await decrement_button.click()

        # Confirm the final quantity
        final_quantity_text = await page.locator(quantity_selector).inner_text()
        final_quantity = int(final_quantity_text.split(": ")[1])

        if final_quantity < quantity:
            await self.raise_http_exception(f"Maximum quantity available is {final_quantity}", status_code=status.HTTP_400_BAD_REQUEST)

    async def _handle_cart_variants(self, matched_index, page: Page, product: Product):
        if matched_index is None:
            await self.raise_http_exception("Product not found in cart", status_code=status.HTTP_404_NOT_FOUND)

        product_variants = product.product_variant
        cart_container = await page.query_selector_all(self.selectors["cart_deletion"]["cart_item_container"])
        for i,cart_item_container in enumerate(cart_container):
            prod_variants = await cart_item_container.query_selector(self.selectors["cart_deletion"]["product_variant"])
            if prod_variants:
                cart_variant_text = await prod_variants.inner_text()
                if "/" in cart_variant_text:
                    price_segment = cart_variant_text.split("$")[1]
                    expected_variant_value = price_segment.split("/")[1].strip()

                    if expected_variant_value == product_variants:
                        matched_index = i
                        print("Product variant match.")
                    else:
                        print("Product variant mismatch.")
                        await self.raise_http_exception("Variant mismatch in cart", status_code=status.HTTP_404_NOT_FOUND)

                else:
                    matched_index = i

    async def _check_not_available(self, page: Page, not_available_selector=str):
        """
        Check if the 'Not available near you' message is present on the page.
        """
        not_available_element = page.locator(not_available_selector)

        is_visible = await not_available_element.is_visible()

        if is_visible:
            await self.raise_http_exception("Not available near you", status_code=status.HTTP_400_BAD_REQUEST)

    async def _click_on_cart(self, page: Page):
        cart_icon = await page.wait_for_selector(self.selectors["cart_verification"]["wait_for_cart_button"])
        if cart_icon:
            await cart_icon.click()

    async def _check_cart_empty(self, page: Page, cart_container: Page):
        # Check if the cart is empty
        empty_cart_message = await cart_container.query_selector(self.selectors["cart_verification"]["empty_cart"])
        if empty_cart_message:
            message_text = await empty_cart_message.inner_text()
            if "Your bag is empty" in message_text:
                await self.raise_http_exception("Your cart is empty", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return cart_container

    async def _get_cart_item_containers(self, page: Page, cart_container: Page):
        if cart_container:
            await page.wait_for_selector(self.selectors["cart_verification"]["cart_item_container"], state="visible", timeout=5000)
            cart_item_containers = await page.query_selector_all(self.selectors["cart_verification"]["cart_item_container"])
            return cart_item_containers

    async def _checkout_checks(self, page):
        # Check for any checkout alerts
        await self._handle_error_notification(
            page,
            notification_selector=self.selectors["checkout"]["error_notification_selector"],
            exc_message="Order submission failed: {}"
        )
        await self._handle_item_option(page)
        await self._click_continue(page, timeout=2000, button_index=0)

    async def _handle_item_option(self, page: Page):
        await page.wait_for_selector(self.selectors["checkout"]["handle_item_option"], timeout=15000)
        pickup_button = page.locator(self.selectors["checkout"]["pickup_button"])
        if await pickup_button.count() > 0:
            try:
                await pickup_button.click(force=True)
            except TimeoutError:
                pass

        await self._handle_error_notification(
            page,
            notification_selector=self.selectors["checkout"]["error_notification_selector_2"],
            exc_message="Order submission failed: {}"
        )

        accordion_container = await page.wait_for_selector(self.selectors["checkout"]["checkboxes_container"], timeout=5000)
        if accordion_container:
            checkboxes = await accordion_container.query_selector_all(self.selectors["checkout"]["checkboxes"])
            for checkbox in checkboxes:
                if not await checkbox.is_checked():
                    await checkbox.click()

    async def _click_continue(self, page: Page, timeout: Optional[int] = 5000,button_index: int = 0):
        continue_buttons = await page.locator(self.selectors["checkout"]["continue_button"]).all()

        if len(continue_buttons) > button_index:
            continue_button = continue_buttons[button_index]  # Select the button based on the index

            # Check if the selected continue button is visible
            await continue_button.wait_for(state='visible', timeout=timeout)

            # Check if the Continue button is disabled
            await asyncio.sleep(3)
            is_disabled = await continue_button.get_attribute("disabled") is not None

            if is_disabled:
                await self._handle_error_notification(
                    page,
                    notification_selector=self.selectors["checkout"]["error_notification_selector"],
                    exc_message="Order submission failed: {}"
                )
                await self.raise_http_exception("User form details not valid", status_code=status.HTTP_400_BAD_REQUEST)
            else:
                await continue_button.click()

    async def _select_payment_option(self, page: Page):
        """
        Custom method for selecting payment option in iHeartJane.
        """
        payments_accordion = await page.wait_for_selector(self.selectors["checkout"]["payments_accordion"], state='visible', timeout=5000)
        if payments_accordion:
            await payments_accordion.click()

        cash_payment_button = await page.wait_for_selector(self.selectors["checkout"]["cash_payment_button"], state='visible', timeout=5000)
        if cash_payment_button:
            await cash_payment_button.click()



    async def _fetch_checkout_options(self, page: Page) -> Dict[str, Any]:
        pickup_button_selector = self.selectors["checkout_fetch"].get("pickup_button")
        selected_order_type = "pickup"

        if pickup_button_selector:
            try:
                pickup_button = await page.wait_for_selector(pickup_button_selector, timeout=5000)
                if await pickup_button.get_attribute("data-selected") == "false":
                    await pickup_button.click()
            except TimeoutError:
                pass

        accordion_content_selector = self.selectors["checkout_fetch"]["accordion_content_selector"]
        accordion_content = await page.wait_for_selector(accordion_content_selector, timeout=5000)

        if not accordion_content:
            return {"error": "Accordion content not found"}

        # Annotate pickup slots with type
        pickup_options_selector = self.selectors["checkout_fetch"]["pickup_options_selector"]
        await page.wait_for_selector(pickup_options_selector, timeout=5000)
        pickup_options_element = await page.query_selector(pickup_options_selector)

        pickup_slots = []
        option_elements = await pickup_options_element.query_selector_all("option")
        for option in option_elements:
            option_text = await option.inner_text()
            pickup_slots.append({"label": option_text, "type": "select"})

        # Annotate pickup instructions with type
        checkbox_selector = self.selectors["checkout_fetch"]["checkbox_selector"]
        checkboxes = await accordion_content.query_selector_all(checkbox_selector)
        for checkbox in checkboxes:
            if not await checkbox.is_checked():
                await checkbox.click()

        pickup_instructions_class = self.selectors["checkout_fetch"]["pickup_instructions_class"]
        pickup_instructions_container = await page.query_selector(pickup_instructions_class)
        pickup_instructions_selector = self.selectors["checkout_fetch"]["pickup_instructions_selector"]

        if not pickup_instructions_container:
            pickup_instructions_texts = [{"label": "Pickup instructions container not found", "type": ""}]
        else:
            pickup_instruction_elements = await pickup_instructions_container.query_selector_all(pickup_instructions_selector)
            pickup_instructions_texts = [{"label": await elem.inner_text(), "type": "checkbox"} for elem in pickup_instruction_elements] if pickup_instruction_elements else [{"label": "No pickup instructions", "type": ""}]

        await self._click_continue(page, timeout=2000, button_index=0)

        accordion_content_info_selector = self.selectors["checkout_fetch"]["accordion_content_info_selector"]
        accordion_content_info = await page.wait_for_selector(accordion_content_info_selector, timeout=5000)

        # Annotate customer info with type
        customer_info = []
        if accordion_content_info:
            label_elem = self.selectors["checkout_fetch"]["label_elem"]
            label_elements = await accordion_content_info.query_selector_all(label_elem)
            for label in label_elements:
                label_text = await label.inner_text()
                customer_info.append({"label": label_text, "type": "input"})

        # Annotate file upload fields
        gov_id_path = "static_file/government_id.jpg"
        med_id_front_path = "static_file/medical_id_front.jpg"
        med_id_back_path = "static_file/medical_id_back.jpg"

        file_paths = [
            {"path": gov_id_path, "label": "Government ID upload required", "type": "file"},
            {"path": med_id_front_path, "label": "Medical front of card upload required", "type": "file"},
            {"path": med_id_back_path, "label": "Medical back of card upload required", "type": "file"},
        ]

        input_selector = self.selectors["checkout_fetch"].get("id_file_input")
        dummy_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'johndoe@example.com',
            'mobile_phone': '1234567890',
            'birthdate': '01/01/1980',
            'mmj_id': str(random.randint(100000000, 999999999))
        }

        for index, file_info in enumerate(file_paths):
            file_path = file_info["path"]

            if os.path.exists(file_path):
                try:
                    file_input = page.locator(input_selector).nth(index)
                    if not await file_input.is_visible(timeout=3000):
                        continue

                    customer_info.append({"label": file_info["label"], "type": file_info["type"]})
                    await file_input.set_input_files(file_path)

                except Exception as e:
                    print(f"Failed to upload file for {file_info['label']}: {e}")

        await self._fill_field(page, self.selectors["checkout_fetch"].get('mmj_id_input'), dummy_data['mmj_id'])
        await self._fill_field(page, self.selectors["checkout_fetch"].get('first_name'), dummy_data['first_name'])
        await self._fill_field(page, self.selectors["checkout_fetch"].get('last_name'), dummy_data['last_name'])
        await self._fill_field(page, self.selectors["checkout_fetch"].get('email'), dummy_data['email'])
        await self._fill_field(page, self.selectors["checkout_fetch"].get('mobile_phone'), dummy_data['mobile_phone'])
        await self._fill_field(page, self.selectors["checkout_fetch"].get('birthdate'), dummy_data['birthdate'])

        await self._click_continue(page, timeout=5000, button_index=1)

        # Annotate payment details with type
        payment_details = []
        payment_accordion_selector = self.selectors["checkout_fetch"]["payment_accordion_selector"]
        payment_accordion = await page.wait_for_selector(payment_accordion_selector, timeout=5000)

        if payment_accordion:
            jane_pay_selector = self.selectors["checkout_fetch"]["jane_pay_selector"]
            jane_pay_option = await payment_accordion.query_selector(jane_pay_selector)
            if jane_pay_option:
                payment_details.append({"label": "JanePay", "type": "radio"})
            
            button_selector = "button"
            payment_buttons = await payment_accordion.query_selector_all(button_selector)
            for button in payment_buttons:
                button_id = await button.get_attribute("data-testid")
                if button_id and button_id != "accordion-item-jane_pay":
                    if "Pay by linking" not in await button.inner_text():
                        button_text = await button.inner_text()
                        payment_details.append({"label": button_text.strip(), "type": "radio"})

        checkout_options = CheckoutOptions(
            pickup_slots=pickup_slots,
            pickup_instructions=pickup_instructions_texts,
            customer_info=customer_info,
            payment_details=payment_details
        )

        return checkout_options.to_dict()

    async def _extract_variation_price_and_msrp(self, page, variation_element):
        product_details = await page.query_selector(self.selectors["variant"]["product_details"])
        price_element = await product_details.query_selector(self.selectors["variant"]["variant_price_selector"])
        return await price_element.inner_text()


