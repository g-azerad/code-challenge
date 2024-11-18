from abc import abstractmethod, abstractproperty
from http.client import HTTPException
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel

class CheckoutOptions:
    def __init__(
        self,
        pickup_slots: Optional[List[str]] = None,
        pickup_instructions: Optional[List[str]] = None,
        customer_info: Optional[List[str]] = None,
        payment_details: Optional[List[str]] = None,
        state_selection: Optional[List[str]] = None,
        order_type_details: Optional[Dict[str, Any]] = None,
        selected_order_data: Optional[Dict[str, Any]] = None,
        extra_fields: Optional[List[str]] = None,
        medical_section_details: Optional[List[str]] = None,
    ):
        self.pickup_slots = pickup_slots or []
        self.pickup_instructions = pickup_instructions or []
        self.customer_info = customer_info or []
        self.payment_details = payment_details or []
        self.state_selection = state_selection or []
        self.order_type_details = order_type_details or {}
        self.selected_order_data = selected_order_data or {}
        self.extra_fields = extra_fields or []
        self.medical_section_details = medical_section_details or []

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "pickup_slots": self.pickup_slots,
            "pickup_instructions": self.pickup_instructions,
            "customer_info": self.customer_info,
            "payment_details": self.payment_details,
            "state_selection": self.state_selection,
            "order_type_details": self.order_type_details,
        }
        
        # Add optional fields if they have data
        if self.selected_order_data:
            data["selected_order_data"] = self.selected_order_data
        if self.extra_fields:
            data["extra_fields"] = self.extra_fields
        if self.medical_section_details:
            data["medical_section_details"] = self.medical_section_details

        return data

class UIField(BaseModel):
    label: str
    selector: str
    required: bool = True

    @abstractmethod
    def get_value(self):
        """Calculate the value for this input"""

class InputField(UIField):
    input: Optional[str] = None
    field_type: str = "input"

    def get_value(self):
        if self.input:
            return self.input
        else:
            raise HTTPException(status_code=400, detail=f"Input field {self.label} needs to specify an 'input'")

class SingleSelectionField(UIField):
    field_type: str = "single_selection"

    options: List[str]
    selected: Optional[int] = None

    def get_value(self):

        if self.selected:
            if self.selected >= 0 & self.selected < len(self.options):
                return self.options[self.selected]
            else:
                raise HTTPException(status_code=400, detail = f"Input field {self.label} ")
        else:
            raise HTTPException(status_code=400, detail=f"Input field {self.label} needs to specify a 'selected' option")

class CustomerInfo(BaseModel):
    fields: List[InputField]

class CheckoutOptionsV2(BaseModel):
    customer_info: CustomerInfo
    order_type: SingleSelectionField
    payment_details: SingleSelectionField
    pickup_slots: SingleSelectionField = None
