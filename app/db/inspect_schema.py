
from sqlalchemy import inspect

from app.db.session import engine


TABLES_TO_INSPECT = [
    "categories",
    "products",
    "product_variants",
    "product_images",
]


def main() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table_name in TABLES_TO_INSPECT:
        print(f"\n{'=' * 60}")
        print(f"TABLE: {table_name}")
        print("=" * 60)

        if table_name not in existing_tables:
            print("Table not found.")
            continue

        print("\nCOLUMNS:")
        for column in inspector.get_columns(table_name):
            print(
                f"  {column['name']}: {column['type']} "
                f"| nullable={column['nullable']} "
                f"| default={column.get('default')}"
            )

        primary_key = inspector.get_pk_constraint(table_name)
        print("\nPRIMARY KEY:")
        print(primary_key.get("constrained_columns"))

        print("\nFOREIGN KEYS:")
        for foreign_key in inspector.get_foreign_keys(table_name):
            print(
                f"  {foreign_key['constrained_columns']} -> "
                f"{foreign_key['referred_table']}."
                f"{foreign_key['referred_columns']}"
            )


if __name__ == "__main__":
    main()
