
import json
from collections.abc import Callable
from decimal import Decimal
from typing import Annotated

from langchain.tools import tool
from pydantic import Field
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.product_repository import ProductRepository


def create_product_search_tool(
    session_factory: Callable[[], Session] = SessionLocal,
):
    """Create a LangChain tool for searching the product catalog."""

    @tool
    def search_products(
        query: Annotated[
            str,
            Field(
                max_length=100,
                description="Product name, brand, or description keywords.",
            ),
        ] = "",
        category_name: Annotated[
            str | None,
            Field(
                max_length=100,
                description=(
                    "Product category name, such as Dresses, Shoes, "
                    "Swimwear, or Accessories. Use only categories "
                    "that exist in the store catalog."
                ),
            ),
        ] = None,
        color: Annotated[
            str | None,
            Field(
                max_length=50,
                description="Desired color, such as black or beige.",
            ),
        ] = None,
        size: Annotated[
            str | None,
            Field(
                max_length=30,
                description="Desired size, such as S, M, L, or 38.",
            ),
        ] = None,
        max_price: Annotated[
            Decimal | None,
            Field(
                gt=0,
                description=(
                    "Maximum catalog price in the catalog's price units. "
                    "Do not assume a currency that has not been confirmed."
                ),
            ),
        ] = None,
        limit: Annotated[
            int,
            Field(
                ge=1,
                le=10,
                description="Maximum number of products to return.",
            ),
        ] = 5,
    ) -> str:
        """Search active store products using text and optional filters.

        Use category_name to restrict results to a product category.
        Use color, size, and max_price to filter active variants.

        Returned prices and stock may be demo data; check their demo
        flags before describing them as confirmed selling prices
        or live availability.
        """

        with session_factory() as db:
            repository = ProductRepository(db)
            products = repository.search_active_products(
                query=query,
                limit=limit,
                category_name=category_name,
                color=color,
                size=size,
                max_price=max_price,
            )

            results = []

            for product in products:
                results.append(
                    {
                        "id": str(product.id),
                        "name": product.name,
                        "description": product.description,
                        "brand": product.brand,
                        "category_id": str(product.category_id),
                        "images": [
                            image.image_url for image in product.images
                        ],
                        "variants": [
                            {
                                "sku": variant.sku,
                                "size": variant.size,
                                "color": variant.color,
                                "attributes": variant.attributes,
                                "price": str(variant.price),
                                "price_is_demo": variant.price_is_demo,
                                "stock_quantity": variant.stock_quantity,
                                "stock_is_demo": variant.stock_is_demo,
                                "images": [
                                    image.image_url
                                    for image in variant.images
                                ],
                            }
                            for variant in product.variants
                        ],
                    }
                )

        return json.dumps(
            {"count": len(results), "products": results},
            ensure_ascii=False,
        )

    return search_products
