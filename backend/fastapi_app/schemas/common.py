from typing import Any

from pydantic import BaseModel, Field


class ApiResponseSchema(BaseModel):
    message: str
    payload: Any
    status_code: int = Field(alias="status code")
