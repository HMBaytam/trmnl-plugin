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


# Shape returned to TRMNL: each item's type field (value/mindset/ritual) is
# normalized to a common `name` key so the Liquid template can treat all three
# uniformly (##{{ value.name }}, ##{{ mindset.name }}, ##{{ ritual.name }}).
class DailyItem(BaseModel):
    name: str
    arabic: Optional[str] = None
    description: str


class DailyBundle(BaseModel):
    date: str  # ISO date (YYYY-MM-DD) in the requested timezone
    value: DailyItem
    mindset: DailyItem
    ritual: DailyItem

