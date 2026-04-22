from typing import Optional, List
from datetime import date
from pydantic import Field, EmailStr
from enum import Enum

from fluvius.dform.element import DataElementModel

class PersonalInfoElement(DataElementModel):
    """Personal information element for collecting name, DOB, etc."""
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    middle_name: Optional[str] = Field(default=None, description="Middle name")
    date_of_birth: Optional[date] = Field(default=None, description="Date of birth")
    gender: Optional[str] = Field(default=None, description="Gender")
    
    class Meta:
        key = "personal-info"
        title = "Personal Information"
        description = "Collects personal information including name and date of birth"
        table_name = "dfe_personal_info"
