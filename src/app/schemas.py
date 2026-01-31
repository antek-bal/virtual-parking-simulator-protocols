from pydantic import BaseModel, Field


class EntryRequest(BaseModel):
    country: str = Field(...)
    registration_no: str = Field(..., min_length=5, max_length=8)
    floor: int = Field(..., ge=0, le=4)


class UpdateFloorRequest(BaseModel):
    new_floor: int = Field(..., ge=0, le=4)


class PaymentRequest(BaseModel):
    amount: float = Field(..., ge=0)
