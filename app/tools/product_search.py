
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
                min_length=1,
                max_length=100,
                description=(
                    "Keywords describing the products the customer wants, "
                    "such as 'black dress' or 'handbag'."
                ),
            ),
        ],
        limit: Annotated[
            int,
            Field(
                ge=1,
                le=10,
                description="Maximum number of products to return.",
            ),
        ] = 5,
    ) -> str:

        with session_factory() as db:
            repository = ProductRepository(db)
            products = repository.search_active_products(
                query=query,
                limit=limit,
            )

            results = []

            for product in products:
                variants = []

                for variant in product.variants:
                    variants.append(
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
                    )

                results.append(
                    {
                        "id": str(product.id),
                        "name": product.name,
                        "description": product.description,
                        "brand": product.brand,
                        "category_id": str(product.category_id),
                        "images": [
                            image.image_url
                            for image in product.images
                        ],
                        "variants": variants,
                    }
                )

        return json.dumps(
            {
                "count": len(results),
                "products": results,
            },
            ensure_ascii=False,
        )

    return search_products
