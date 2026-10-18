
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductResponse


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductResponse])
def search_products(
    db: Annotated[Session, Depends(get_db)],
    query: Annotated[str, Query(max_length=100)] = "",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    category_id: UUID | None = None,
) -> list[ProductResponse]:
    """Search the active product catalog."""

    repository = ProductRepository(db)

    products = repository.search_active_products(
        query=query,
        limit=limit,
        category_id=category_id,
    )

    return [
        ProductResponse.model_validate(product)
        for product in products
    ]
