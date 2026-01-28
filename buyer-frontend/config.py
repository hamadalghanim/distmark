from sqlalchemy import create_engine
from db import BaseCustomers

products_engine = create_engine(
    "postgresql+psycopg2://user:pass@products-database:5432/products", pool_size=20, max_overflow=0
)

customers_engine = create_engine(
    "postgresql+psycopg2://user:pass@customers-database:5432/customers", pool_size=20, max_overflow=0
)
BaseCustomers.metadata.create_all(customers_engine)
