from typing import Optional, List
from datetime import date
from pydantic import Field, EmailStr
from enum import Enum

from fluvius.dform.element import DataElementModel

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

class TextInputElementModel(DataElementModel):
    """A simple text input element"""
    value: str = Field(default="", description="The text input value")
    placeholder: Optional[str] = Field(default=None, description="Placeholder text")
    max_length: Optional[int] = Field(default=None, description="Maximum character length")
    
    class Meta:
        key = "text-input"
        title = "Text Input"
        description = "A single-line text input element"
        table_name = "text_input_element"


class NumberInputElementModel(DataElementModel):
    """A number input element with min/max bounds"""
    value: float = Field(default=0.0, description="The numeric value")
    min_value: Optional[float] = Field(default=None, description="Minimum allowed value")
    max_value: Optional[float] = Field(default=None, description="Maximum allowed value")
    step: Optional[float] = Field(default=1.0, description="Step increment")
    
    class Meta:
        key = "number-input"
        title = "Number Input"
        description = "A numeric input element with optional bounds"
        table_name = "number_input_element"


class SelectElementModel(DataElementModel):
    """A select/dropdown element"""
    value: str = Field(default="", description="The selected value")
    options: List[str] = Field(default_factory=list, description="Available options")
    allow_multiple: bool = Field(default=False, description="Allow multiple selections")
    
    class Meta:
        key = "select"
        title = "Select"
        description = "A dropdown selection element"
        table_name = "select_element"

