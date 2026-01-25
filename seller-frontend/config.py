from sqlalchemy import create_engine
from db import BaseProducts
from seed import seed

# customer_db = DatabaseConnection(
#     db_name="customers",
#     user="user",
#     password="pass",
#     host="customers-database",  # Updated to connect to the correct database service
#     port=5432,
# )
# customer_db.connect()
products_engine = create_engine(
    "postgresql://user:pass@products-database:5432/products", echo=True
)

seed(products_engine)
