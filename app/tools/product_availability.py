
import json

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from langchain.tools import tool
from pydantic import Field
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.product_variant import ProductVariant
from app.repositories.product_repository import ProductRepository

def create_product_availability_tool(
    session_factory: Callable[[], Session] = SessionLocal,
):
    """Create a LangChain tool for checking product variant availability."""

    @tool
    def check_product_availability(
        product_id: Annotated[
            UUID,
            Field(description="Exact product UUID from catalog search results."),
        ],
        color: Annotated[
            str | None,
            Field(description="Optional color to check."),
        ] = None,
        size: Annotated[
            str | None,
            Field(description="Optional size to check."),
        ] = None,
    ) -> str:
        """Check matching variants and their stock verification status.

        Never claim live availability when stock_is_demo is true.
        """

        with session_factory() as session:
            repository = ProductRepository(session)
            product , variants = repository.get_product_with_variants(
                product_id=product_id,
                color=color,
                size=size,
            )

        if product is None:
            result ={
                "found": False,
                "message": "Product not found in catalog or inactive.",
                "variants": [],
            }
        else:
            result = {
                    "found": True,
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "matching_variant_count": len(variants),
                    "variants": [
                        {
                            "sku": variant.sku,
                            "color": variant.color,
                            "size": variant.size,
                            "stock_quantity": variant.stock_quantity,
                            "stock_is_demo": variant.stock_is_demo,
                            "stock_status": (
                                "demo_data"
                                if variant.stock_is_demo
                                else "not_marked_demo"
                            ),
                        }
                        for variant in variants
                    ],
            }
            return json.dumps(result, ensure_ascii=False)
        
        return check_product_availability