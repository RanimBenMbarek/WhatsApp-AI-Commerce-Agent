
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductImageResponse(BaseModel):
    """Public image information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    image_url: str
    alt_text: str | None
    sort_order: int


class ProductVariantResponse(BaseModel):
    """Public information about a purchasable product variant."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    size: str | None
    color: str | None
    attributes: dict[str, object]
    price: Decimal
    stock_quantity: int
    price_is_demo: bool
    stock_is_demo: bool
    images: list[ProductImageResponse] = Field(default_factory=list)


class ProductResponse(BaseModel):
    """Public product representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    brand: str | None
    category_id: UUID
    variants: list[ProductVariantResponse] = Field(default_factory=list)
    images: list[ProductImageResponse] = Field(default_factory=list)
