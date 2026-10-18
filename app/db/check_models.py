
from sqlalchemy import inspect

from app.db.base import Base
import app.models   


def main() -> None:
    for table_name, table in Base.metadata.tables.items():
        print(f"\nTable: {table_name}")
        print(f"Columns: {list(table.columns.keys())}")

    for model_name in ("Product", "Category", "ProductVariant", "ProductImage"):
        model = getattr(app.models, model_name)
        mapper = inspect(model)
        print(f"\n{model_name} relationships:")
        print(list(mapper.relationships.keys()))


if __name__ == "__main__":
    main()
