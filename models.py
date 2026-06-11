from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field

pyObjectId = Annotated[str, BeforeValidator(str)]


class BarakahCard(BaseModel):
    id: pyObjectId = Field(default=None, alias="_id")
    value: str
    arabic: Optional[str] = None
    description: str

