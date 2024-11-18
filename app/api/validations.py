
from pydantic import BaseModel, Field, EmailStr, field_validator, ValidationError
from fastapi import Form, HTTPException, Depends ,status
import re
from typing import Optional
from datetime import datetime

class SubmitOrderForm(BaseModel):
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    mobile_phone: str = Field(..., description="10-digit US mobile phone number")
    birthdate: str = Field(..., description="Birthdate in MM/DD/YYYY format")
    email: EmailStr  # EmailStr will validate the email format
    state: str = Field(..., description="State of residence")
    promo_code: Optional[str] = None
    medical_card_number: Optional[str] = None
    medical_card_expiration: Optional[str] = None
    medical_card_state: Optional[str] = None


    @field_validator("mobile_phone")
    def validate_mobile_phone(cls, value):
        if not re.fullmatch(r"^[2-9]\d{2}[2-9]\d{6}$", value):
            raise HTTPException(detail="Invalid mobile phone number. Must be a 10-digit US number.",status_code=status.HTTP_400_BAD_REQUEST)
        return value

    @field_validator("birthdate")
    def validate_birthdate(cls, value):
        try:
            datetime.strptime(value, "%m/%d/%Y")
        except ValueError:
            raise HTTPException(detail="Invalid birthdate format. Must be in MM/DD/YYYY format.",status_code=status.HTTP_400_BAD_REQUEST)
        return value

    @classmethod
    def as_form(
        cls,
        first_name: str = Form(...),
        last_name: str = Form(...),
        mobile_phone: str = Form(...),
        birthdate: str = Form(...),
        email: str = Form(...),
        state: str = Form(...),
        promo_code: str = Form(None),
        medical_card_number: str = Form(None),
        medical_card_expiration: str = Form(None),
        medical_card_state: str = Form(None),
    ):
        return cls(
            first_name=first_name,
            last_name=last_name,
            mobile_phone=mobile_phone,
            birthdate=birthdate,
            email=email,
            state=state,
            promo_code=promo_code,
            medical_card_number=medical_card_number,
            medical_card_expiration=medical_card_expiration,
            medical_card_state=medical_card_state,
        )

