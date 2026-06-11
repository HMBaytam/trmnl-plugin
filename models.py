from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field

pyObjectId = Annotated[str, BeforeValidator(str)]


class BarakahBase(BaseModel):
    id: pyObjectId = Field(default=None, alias="_id")
    arabic: Optional[str] = None
    description: str


class BarakahValue(BarakahBase):
    value: str


class BarakahMindset(BarakahBase):
    mindset: str


class BarakahRitual(BarakahBase):
    ritual: str

