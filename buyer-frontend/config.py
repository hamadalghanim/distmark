from sqlalchemy import create_engine
from db import BaseCustomers

products_engine = create_engine(
    "postgresql://user:pass@products-database:5432/products", echo=True
)

customers_engine = create_engine(
    "postgresql://user:pass@customers-database:5432/customers", echo=True
)
BaseCustomers.metadata.create_all(customers_engine)
