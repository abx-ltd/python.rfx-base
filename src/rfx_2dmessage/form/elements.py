from typing import Optional, List
from datetime import date
from pydantic import Field, EmailStr
from enum import Enum

from fluvius.dform.element import DataElementModel

class PersonalInfoElement(DataElementModel):
    """Personal information element for collecting name, DOB, etc."""
    first_name: str = Field(description="First name")
    
    class Meta:
        key = "personal-info"
        title = "Personal Information"
        description = "Collects personal information including name and date of birth"


class text(DataElementModel):
    text: str = Field(description="text")

    class Meta:
        key = "text"
        title = "lable"