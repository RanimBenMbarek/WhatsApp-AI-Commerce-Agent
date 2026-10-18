
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Product, ProductVariant


class ProductRepository:
    """Database access for the product catalog."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def search_active_products(
        self,
        query: str = "",
        limit: int = 10,
        category_id: UUID | None = None,
    ) -> list[Product]:
        """Search active products and load their related catalog data."""

        statement = (
            select(Product)
            .where(Product.status == "active")
            .order_by(Product.name.asc())
            .options(
                selectinload(
                    Product.variants.and_(
                        ProductVariant.is_active.is_(True)
                    )
                ).selectinload(ProductVariant.images),
                selectinload(Product.images),
            )
        )

        search_text = query.strip()

        if search_text:
            escaped_query = (
                search_text
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            pattern = f"%{escaped_query}%"

            statement = statement.where(
                or_(
                    Product.name.ilike(pattern, escape="\\"),
                    Product.brand.ilike(pattern, escape="\\"),
                    Product.description.ilike(pattern, escape="\\"),
                )
            )

        if category_id is not None:
            statement = statement.where(
                Product.category_id == category_id
            )

        safe_limit = max(1, min(limit, 50))
        statement = statement.limit(safe_limit)

        result = self.db.scalars(statement)
        return list(result.all())
