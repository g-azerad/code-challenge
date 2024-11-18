import json

from app.handlers.base_handler import BaseHandlerRefactor
from app.services.selectors_service import SelectorsService
from playwright.async_api import Page
from typing import Dict, Optional, Any, List
from app.model.models import Product
from app.model.checkout_options import CheckoutOptions, CheckoutOptionsV2
from fastapi import status


class DutchieHandler(BaseHandlerRefactor):
    """
    Dutchie Cart Handler - Handles adding products to the cart on the Dutchie website.
    """

    def __init__(self):
        self.bot_name = "dutchie"
        super().__init__()

    def _get_bot_name(self):
        return "dutchie"

    def _get_checkout_selectors(self):
        return {
            'first_name': self.selectors["checkout"]["first_name"],
            'last_name': self.selectors["checkout"]["last_name"],
            'email': self.selectors["checkout"]["email"],
            'mobile_phone': self.selectors["checkout"]["mobile_phone"],
            'birthdate': self.selectors["checkout"]["birthdate"],
        }

    async def _checkout_checks(self, page):
        pass

    async def _place_order_details(self, page: Page, user_info: Dict[str, Any]):
        # Handle state selection
        await self._select_state(page, user_info["state"])

        # Handle rewards popup if it appears
        await self._handle_rewards_popup(page)

        # Select order type using dynamic selector
        order_type_selectors = {'order_type': self.selectors["checkout"]["order_type_save_button"]}
        await self._choose_order_type(page, order_type_selectors)

        # Select payment method using dynamic selector
        payment_method_selectors = {'payment_method_selectors': self.selectors["checkout"]["payment_method_save_button"]}
        await self._choose_payment_method(page, payment_method_selectors, "creditCard" )
        

        # Select order time (custom logic for Dutchie)
        await self._select_order_time(page)

        # Apply promo code if provided using dynamic selector
        await self._apply_promo_code(page, user_info.get("promo_code"))

        # Get order details dynamically
        order_details = await self._get_order_details(page)

        # Place the order using dynamic selector
        submit_selectors = {
            'place_order': self.selectors["checkout"]["place_order"],
            'order_success': self.selectors["checkout"]["successful_message"]
        }

        # Place the order
        await self._place_order(page, submit_selectors)

        return order_details

    async def _place_order_details_v2(self, page: Page, checkout_options: CheckoutOptionsV2):
        # Handle state selection
        state = next(field for field in checkout_options.customer_info.fields if field.label == "state").get_value()
        await self._select_state(page, state)

        # Handle rewards popup if it appears
        await self._handle_rewards_popup(page)

        # Select order type using dynamic selector
        order_type_selectors = {'order_type': self.selectors["checkout"]["order_type_save_button"]}
        await self._choose_order_type(page, order_type_selectors)

        # Select payment method using dynamic selector
        payment_method_selectors = {'payment_method_selectors': self.selectors["checkout"]["payment_method_save_button"]}
        payment_method_type = checkout_options.payment_details.get_value()
        await self._choose_payment_method(page, payment_method_selectors, payment_method_type)

        # Select order time (custom logic for Dutchie)
        await self._select_order_time(page)

        # Skipping for V2 since we don't really need to worry about promo codes yet
        # Apply promo code if provided using dynamic selector
        # await self._apply_promo_code(page, user_info.get("promo_code"))

        # Get order details dynamically
        order_details = await self._get_order_details(page)

        # Place the order using dynamic selector
        submit_selectors = {
            'place_order': self.selectors["checkout"]["place_order"],
            'order_success': self.selectors["checkout"]["successful_message"]
        }

        # Place the order
        await self._place_order(page, submit_selectors)

        return order_details

    async def _initial_checks(self, page: Page):
        # Handle age restriction: The loading time for age restriction prompts can vary depending on browser and location settings.
        # To ensure consistency, set a more restrictive timeout of 3 seconds.
        await self._handle_extra_modal(
            page,
            modal_selector=self.selectors["add_to_cart"]["age_rstr_container"],
            button_selector=self.selectors["add_to_cart"]["age_rstr_btn"],
            timeout=3000
        )

    async def _handle_cart_variants(self, matched_product, matched_index, page: Page, product_url: str, product: Product):
        if not matched_product:
            await self.raise_http_exception("Product not found in cart", status_code=status.HTTP_404_NOT_FOUND)

        product_variants = product.product_variant

        try:
            product_variant = await page.query_selector(self.selectors["cart_deletion"]["product_variant"])

            if product_variant:
                cart_variant_text = await product_variant.inner_text()

                if product_variants and cart_variant_text != product_variants:
                    await self.raise_http_exception("Variant mismatch in cart", status_code=status.HTTP_404_NOT_FOUND)
            else:
                print("No product variant found in the cart. Proceeding with deletion based on product name.")
        except TimeoutError:
            print("Product variant not found or timed out. Proceeding without variant check.")   

    async def _bag_check(self, page: Page):
        # Dispensary closed-but modal check
        await self._handle_extra_modal(
            page,
            modal_selector=self.selectors["add_to_cart"]["closed_but_modal_selector"],
            button_selector=self.selectors["add_to_cart"]["closed_but_modal_selector_continue"].split(" ")[-1],
            timeout=2000
        )

        # Dispensary closed modal check
        await self._handle_imp_modal(
            page,
            modal_selector=self.selectors["add_to_cart"]["fully_closed_modal_selector"],
            exc_message="Dispensary is closed, cannot add to cart",
            timeout=2000
        )

        # Modal check for other dispensary products in cart
        await self._handle_imp_modal(
            page,
            modal_selector=self.selectors["add_to_cart"]["clear_cart_selector"],
            exc_message="Clear the cart before adding products from a new dispensary",
            timeout=2000
        )

        # Minimum purchase limit notification check
        await self._handle_error_notification(
            page,
            notification_selector=self.selectors["add_to_cart"]["purchase_limit_selector"],
            exc_message="Minimum purchase limit reached: {}"
        )

    async def _select_quantity(self, page: Page, quantity: int, exst_quantity: Optional[int]):
        """
        Selects quantity of products to be added to the cart
        """
        selector = self.selectors["add_to_cart"]["desired_quantity"]

        # Open quantity selector
        quantity_elm = await page.wait_for_selector(self.selectors["add_to_cart"]["quantity_selector"], state="visible", timeout=2000)
        await quantity_elm.click()
        await page.wait_for_selector(self.selectors["add_to_cart"]["quantity_selector_wait_for"])

        # Get available quantities
        quantity_options = await page.query_selector_all(self.selectors["add_to_cart"]["available_quantities"])
        available_quantities = [int(await option.get_attribute("data-value")) for option in quantity_options]

        if quantity not in available_quantities:
            await self.raise_http_exception(f"Maximum quantity available is {available_quantities[-1]}",
                                            status_code=status.HTTP_400_BAD_REQUEST)
        try:
            quantity_elm = await page.wait_for_selector(selector.format(quantity),timeout=2000)
            await quantity_elm.click()
        except TimeoutError:
            await self.raise_http_exception(
                f"Failed to select quantity: {quantity}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    async def _click_on_cart(self, page: Page):
        cart_container = await page.wait_for_selector(self.selectors["cart_verification"]["wait_for_cart_button"])

        cart_buttons = await page.query_selector_all(self.selectors["cart_verification"]["click_on_cart_button"])
        if cart_buttons:
            await cart_buttons[0].click()

    async def _check_cart_empty(self, page: Page, cart_container: Page):
        # Check if the cart is empty
        # Check if the cart is empty using has-text directly in the selector
        empty_cart_message = await page.query_selector(self.selectors["cart_verification"]["empty_cart"])
        if empty_cart_message:
            await self.raise_http_exception("Your cart is empty", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return await page.query_selector_all(self.selectors["cart_verification"]["wait_for_cart_container"])

    async def _get_cart_item_containers(self, page: Page, cart_container: Page):
        cart_container = await page.query_selector_all(self.selectors["cart_verification"]["wait_for_cart_container"])
        return cart_container

    async def _select_state(self, page: Page, state: str):
        """
        Custom method to select the state (specific to Dutchie).
        """
        state_selector = page.locator(self.selectors["checkout"]["state_selector"])

        if await state_selector.is_visible(timeout=2000):
            await state_selector.click()
            await state_selector.type(state.lower())

    async def _handle_rewards_popup(self, page: Page):
        """
        Handles the rewards popup that may appear on Dutchie.
        """
        rewards_popup = page.locator(self.selectors["checkout"]["rewards_popup"])
        if await rewards_popup.is_visible(timeout=20000):
            print("'Connect to Rewards' popup has appeared.")

    async def _select_order_time(self, page: Page):
        """
        Custom method for selecting order time in Dutchie.
        """
        control_div = page.locator(self.selectors["checkout"]["control_div_order_time"])
        if await control_div.is_visible(timeout=2000):
            await control_div.click()
            menu_div = page.locator(self.selectors["checkout"]["menu_div_order_time"])
            if await menu_div.is_visible(timeout=2000):
                first_option = menu_div.locator(self.selectors["checkout"]["first_option_order_time"]).first
                if await first_option.is_visible(timeout=2000):
                    await first_option.click()

        save_order_time_button = page.locator(self.selectors["checkout"]["save_order_time_button"])
        if await save_order_time_button.is_visible(timeout=2000):
            await save_order_time_button.click()

    async def _apply_promo_code(self, page: Page, promo_code: Optional[str]):
        if promo_code:
            await page.click(self.selectors["checkout"]["promo_code"])
            await page.fill(self.selectors["checkout"]["promo_code_input_fill"], promo_code)
            await page.click(self.selectors["checkout"]["promo_code_button"])

    async def _get_order_details(self, page: Page) -> Dict[str, str]:
        """
        Extracts order details (subtotal, taxes, order total, etc.) for Dutchie.
        """
        details = {}
        subtotal_locator = page.locator(self.selectors["checkout"]["subtotal_locator"])
        if await subtotal_locator.is_visible(timeout=2000):
            details["subtotal"] = await subtotal_locator.inner_text()

        taxes_locator = page.locator(self.selectors["checkout"]["taxes_locator"])
        if await taxes_locator.is_visible(timeout=2000):
            details["taxes"] = await taxes_locator.inner_text()

        order_total_locator = page.locator(self.selectors["checkout"]["order_total_locator"])
        if await order_total_locator.is_visible(timeout=2000):
            details["order_total"] = await order_total_locator.inner_text()

        pickup_method_locator = page.locator(self.selectors["checkout"]["pickup_method_locator"])
        if await pickup_method_locator.is_visible(timeout=2000):
            details["order_type"] = (await pickup_method_locator.inner_text()).strip()
        else:
            details["order_type"] = "Pickup"

        payment_method_locator = page.locator(self.selectors["checkout"]["payment_method_locator"])
        if await payment_method_locator.is_visible(timeout=2000):
            details["payment_type"] = (await payment_method_locator.inner_text()).strip()
        else:
            details["payment_type"] = "Cash"

        pickup_time_locator = page.locator(self.selectors["checkout"]["pickup_time_locator"])
        if await pickup_time_locator.is_visible(timeout=2000):
            details["pickup_time"] = (await pickup_time_locator.inner_text()).strip()

        return details
    
    async def _fetch_checkout_options(self, page: Page) -> Dict[str, Any]:
        section_selector = await page.query_selector(self.selectors["checkout_fetch"]["section_selector"])
        if not section_selector:
            await self.raise_http_exception("Checkout section not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Annotate customer info fields with label and type
        section_elements = await section_selector.query_selector_all("input")
        customer_info = [
            {"label": await input_element.get_attribute('name') or await input_element.get_attribute('id'), "type": "input"}
            for input_element in section_elements if input_element
        ]

        # Annotate state selection options with type 'select'
        state_selection_selector = self.selectors["checkout_fetch"].get("state_selection_selector")
        state_options = []

        state_selection = await page.query_selector(state_selection_selector)
        if state_selection:
            options = await state_selection.query_selector_all("option")
            for option in options:
                option_value = await option.get_attribute("value")
                option_text = await option.inner_text()
                if option_value:
                    state_options.append({"label": option_text, "type": "select"})

        change_button_selector = self.selectors["checkout_fetch"]["change_button"]
        change_button = await page.query_selector(change_button_selector)
        if change_button:
            await change_button.click()

        # Handling order type radio buttons
        order_type_section_selector = self.selectors["checkout_fetch"]["order_type_section"]
        order_type_section = await page.wait_for_selector(order_type_section_selector, timeout=5000)

        radio_options = self.selectors["checkout_fetch"]["order_type_radio"]
        radio_option_elements = await order_type_section.query_selector_all(radio_options)

        order_type_details = {}
        final_data = {"Order_type_details": order_type_details}

        for option in radio_option_elements:
            value = await option.get_attribute("value")
            aria_checked = await option.get_attribute("aria-checked")
            # Attempt to retrieve the type attribute, with a fallback
            input_type = await option.get_attribute("type")

            # Default to a more general type if type is None or unrecognized
            input_type = input_type if input_type in ["radio", "checkbox", "text"] else "text"

            label_elem = self.selectors["checkout_fetch"]["get_extra_value"]
            label_element = await option.query_selector(label_elem)
            label_text = await label_element.inner_text() if label_element else value

            # Construct order_type_details with the dynamically detected type
            order_type_details[value] = {
                "label": label_text,
                "type": input_type,
                "checked": aria_checked == "true"
            }


            if aria_checked == "true":
                selected_order_data = await self._fetch_payment_and_schedules(page, value)

                extra_fields = await self._fetch_additional_fields(page)
                if extra_fields:
                    selected_order_data["Address_Details"] = extra_fields
                    
                medical_section_details = await self.fetch_medical_section_details(page)
                if medical_section_details:
                    selected_order_data["Medical_details"] = medical_section_details

                final_data[value] = selected_order_data
            elif aria_checked == "false":
                try:
                    await option.scroll_into_view_if_needed()
                    is_disabled = await option.get_attribute("disabled")
                    if is_disabled is not None:
                        order_type_details[value]["label"] += " (disabled)"
                        continue
                    await option.click(force=True)

                    selected_order_data = await self._fetch_payment_and_schedules(page, value)

                    extra_fields = await self._fetch_additional_fields(page)
                    if extra_fields:
                        selected_order_data["Address_Details"] = extra_fields

                    medical_section_details = await self.fetch_medical_section_details(page)
                    if medical_section_details:
                        selected_order_data["Medical_details"] = medical_section_details

                    final_data[value] = selected_order_data
                except Exception as e:
                    print(f"Failed to click on {value}: {str(e)}")

        checkout_options = CheckoutOptions(
            customer_info=customer_info,
            state_selection=state_options,
            order_type_details=final_data["Order_type_details"],
            medical_section_details=medical_section_details,
            payment_details=final_data["pickup"]["Payment_details"],
            pickup_slots=final_data["pickup"]["Scheduled_orders"]["Scheduled"]["time_slots"]
        )

        return checkout_options.to_dict()

    async def _fetch_payment_and_schedules(self, page: Page, order_type: str) -> Dict[str, Any]:
        payment_details = []
        payment_section_selector = self.selectors["checkout_fetch"]["payment_delivery_section"]
        payment_section = None

        # Find the payment section
        for selector in payment_section_selector:
            if selector:
                payment_section = await page.query_selector(selector)
                if payment_section:
                    break

        if payment_section:
            payment_types = self.selectors["checkout_fetch"].get("payment_type")
            payment_type_elements = await payment_section.query_selector_all(payment_types)
            if not payment_type_elements:
                payment_types = self.selectors["checkout_fetch"].get("payment_option")
                payment_type_elements = await payment_section.query_selector_all(payment_types)

            for payment in payment_type_elements:
                is_disabled = await payment.get_attribute("disabled")
                payment_type_attr = await payment.get_attribute("type") or "text"

                if payment_types == self.selectors["checkout_fetch"].get("payment_option"):
                    value = await payment.text_content()
                else:
                    value = await payment.get_attribute("value")
                    
                # Define label and type for each payment option
                payment_option = {"label": value, "type": payment_type_attr}
                
                if is_disabled is not None:
                    payment_option["label"] += " (disabled)"
                payment_details.append(payment_option)

        # Fetch scheduled orders data
        scheduled_orders = {}
        scheduled_option_selector = self.selectors["checkout_fetch"]["scheduled_option"]
        scheduled_option = await page.query_selector(scheduled_option_selector)

        day_options = []
        time_slots = []

        if scheduled_option:
            scheduled_radio_group_selector = self.selectors["checkout_fetch"]["radio_group"]
            scheduled_radio_elements = await page.query_selector_all(scheduled_radio_group_selector)
            
            for scheduled_radio in scheduled_radio_elements:
                if scheduled_radio:
                    scheduled_label_element = self.selectors["checkout_fetch"]["get_extra_value"]
                    scheduled_label_elem = await scheduled_radio.query_selector(scheduled_label_element)
                    scheduled_label_text = await scheduled_label_elem.inner_text() if scheduled_label_elem else ""
                    scheduled_aria_checked = await scheduled_radio.get_attribute("aria-checked")
                    is_disabled = await scheduled_radio.get_attribute("disabled")

                    if is_disabled is not None:
                        scheduled_label_text = f"{scheduled_label_text} (disabled)"
                    
                    if ("asap" in scheduled_label_text.lower() or "ASAP" in scheduled_label_text.upper()) and scheduled_aria_checked == "true":
                        scheduled_orders["ASAP"] = scheduled_label_text
                    
                    if "Scheduled" in scheduled_label_text and scheduled_aria_checked == "false":
                        scheduled_orders["Scheduled"] = scheduled_label_text
                        await scheduled_radio.click(force=True)

            # Fetch day options
            day_arrow_selector = self.selectors["checkout_fetch"].get("day_arrow_selector")
            day_arrow = await page.query_selector(day_arrow_selector)
            
            if day_arrow:
                await day_arrow.click()
                day_option_selector = self.selectors["checkout_fetch"].get("day_option")
                day_option_elements = await page.query_selector_all(day_option_selector)
                day_options = [{"label": await day_option.inner_text(), "type": "select"} for day_option in day_option_elements]

            # Fetch time slot options
            time_arrow_selector = self.selectors["checkout_fetch"]["time_arrow_selector"]
            time_arrow_elements = await page.query_selector_all(time_arrow_selector)
            
            if time_arrow_elements:
                time_arrow_to_click = time_arrow_elements[1] if len(time_arrow_elements) > 1 else time_arrow_elements[0]
                await time_arrow_to_click.click()
                await page.wait_for_timeout(1000)

                time_option_selector = self.selectors["checkout_fetch"]["time_options"]
                time_option_elements = await page.query_selector_all(time_option_selector)

                if not time_option_elements:
                    await time_arrow_to_click.click()
                    await page.wait_for_timeout(1000)
                    time_option_elements = await page.query_selector_all(time_option_selector)

                if time_option_elements:
                    time_slots = [{"label": await time_option.inner_text(), "type": "select"} for time_option in time_option_elements]

        if day_options or time_slots:
            scheduled_orders["Scheduled"] = {
                                "days": day_options if day_options else [],
                                "time_slots": time_slots if time_slots else []
                            }

        result = {
            "Payment_details": payment_details
        }
        if scheduled_orders:
            result["Scheduled_orders"] = scheduled_orders

        return result

    async def _fetch_additional_fields(self, page: Page) -> List[Dict[str, str]]:
        extra_fields = []
        
        address_field_selector = self.selectors["checkout_fetch"].get("delivery_address_input")
        if address_field_selector:
            address_input_element = await page.query_selector(address_field_selector)
            if address_input_element:
                address_label = await address_input_element.inner_text()
                extra_fields.append({"label": address_label, "type": "input"})

        apartment_field_selector = self.selectors["checkout_fetch"].get("apartment_number_input")
        if apartment_field_selector:
            apartment_input_element = await page.query_selector(apartment_field_selector)
            if apartment_input_element:
                apartment_label = await apartment_input_element.inner_text()
                extra_fields.append({"label": apartment_label, "type": "input"})

        return extra_fields

    async def fetch_medical_section_details(self, page: Page) -> Dict[str, Any]:
        label_texts = []
        medical_section_selector = self.selectors["checkout_fetch"].get("medical_section_selector")
        change_button_selector = self.selectors["checkout_fetch"].get("change_button_selector")
        expanded_details_selector = self.selectors["checkout_fetch"].get("expanded_details_selector")
        label_selector = "label"

        medical_section = await page.query_selector(medical_section_selector)
        if medical_section:
            change_button = await medical_section.query_selector(change_button_selector)
            if change_button:
                await change_button.click()

            expanded_details = await page.wait_for_selector(expanded_details_selector, timeout=5000)
            if expanded_details:
                labels = await expanded_details.query_selector_all(label_selector)
                # Annotate each label with a type
                label_texts = [{"label": await label.inner_text(), "type": "input"} for label in labels]

        return label_texts

    async def _extract_variation_price_and_msrp(self, page, variation_element):
        # Extract price
        variant_price_selector = self.selectors["variant"]["price_selectors"].get("variant")
        price_element = None

        if variant_price_selector:
            price_element = await variation_element.query_selector(variant_price_selector)

        if not price_element:
            non_variant_price_selector = self.selectors["variant"]["price_selectors"].get("non_variant")
            if non_variant_price_selector:
                price_element = await page.query_selector(non_variant_price_selector)

        price_text = await price_element.inner_text() if price_element else None

        # Extract MSRP
        variant_msrp_selector = self.selectors["variant"]["msrp_selectors"].get("variant")
        msrp_element = None

        if variant_msrp_selector:
            msrp_element = await variation_element.query_selector(variant_msrp_selector)

        if not msrp_element:
            non_variant_msrp_selector = self.selectors["variant"]["msrp_selectors"].get("non_variant")
            if non_variant_msrp_selector:
                msrp_element = await page.query_selector(non_variant_msrp_selector)

        msrp_text = await msrp_element.inner_text() if msrp_element else None

        return {
            "price": price_text,
            "msrp": msrp_text
        }
