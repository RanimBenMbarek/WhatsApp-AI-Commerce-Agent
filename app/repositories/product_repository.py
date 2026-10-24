
from decimal import Decimal
from uuid import UUID

from sqlalchemy import  and_, func, or_, select
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
        color: str | None = None,
        size: str | None = None,
        max_price: Decimal | None = None,
    ) -> list[Product]:
        """Search active products and optionally filter their variants."""

        variant_conditions = [ProductVariant.is_active.is_(True)]

        if color and color.strip():
            color_pattern = (
                color.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            variant_conditions.append(
                ProductVariant.color.ilike(
                    f"%{color_pattern}%",
                    escape="\\",
                )
            )

        if size and size.strip():
            variant_conditions.append(
                ProductVariant.size.ilike(size.strip())
            )

        if max_price is not None:
            variant_conditions.append(
                ProductVariant.price <= max_price
            )

        matching_variants = and_(*variant_conditions)

        statement = (
            select(Product)
            .where(Product.status == "active")
            .order_by(Product.name.asc())
            .options(
                selectinload(
                    Product.variants.and_(matching_variants)
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

        # If variant filters were provided, the product must have
        # at least one active variant satisfying all of them.
        has_variant_filters = any(
            value is not None and (
                not isinstance(value, str) or value.strip()
            )
            for value in (color, size, max_price)
        )

        if has_variant_filters:
            statement = statement.where(
                Product.variants.any(matching_variants)
            )

        safe_limit = max(1, min(limit, 50))
        statement = statement.limit(safe_limit)

        return list(self.db.scalars(statement).all())

    def get_variants_by_conditions(
        self,
        product_id: UUID,
        color: str | None = None,
        size: str | None = None,
    ) -> list[Product | None,list[ProductVariant]]:
        """Retrieve an active product and its matching active variants."""

        product= self.db.scalars(
            select(Product).where(
                Product.id == product_id,
                Product.status == "active",
            )
        )

        if product is None:
            return None, []

        conditions = [ProductVariant.product_id == product_id, ProductVariant.is_active.is_(True)]
        
        if color and color.strip():
            conditions.append(
                func.lower(ProductVariant.color) == color.strip().lower()
            )

        if size and size.strip():
            conditions.append(
                func.lower(ProductVariant.size) == size.strip().lower()
            )

        variants = list(
            self.db.scalars(
                select(ProductVariant)
                .where(*conditions)
                .order_by(
                    ProductVariant.color,
                    ProductVariant.size,
                )
            ).all()
        )


        return product, variants