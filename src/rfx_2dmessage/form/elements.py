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

class ShortAnswerElement(DataElementModel):
    value: str = Field(default="", description="Short answer text")

    class Meta:
        key = "short-answer"
        title = "Short Answer"
        description = "Single line text input"

class ParagraphElement(DataElementModel):
    value: str = Field(default="", description="Long text")

    class Meta:
        key = "paragraph"
        title = "Paragraph"
        description = "Multi-line text input"

class MultipleChoiceElement(DataElementModel):
    value: str = Field(default="")
    options: list[str] = Field(default_factory=list)

    class Meta:
        key = "multiple-choice"
        title = "Multiple Choice"

class CheckboxElement(DataElementModel):
    values: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)

    class Meta:
        key = "checkbox"
        title = "Checkbox"

class DropdownElement(DataElementModel):
    value: str = Field(default="")
    options: list[str] = Field(default_factory=list)

    class Meta:
        key = "dropdown"
        title = "Dropdown"
class text(DataElementModel):
    text: str = Field(description="text")

    class Meta:
        key = "text"
        title = "lable"
        description = "File input for text"
