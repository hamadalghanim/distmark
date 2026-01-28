from sqlalchemy import create_engine
from db import BaseProducts
from seed import seed

products_engine = create_engine(
    "postgresql+psycopg2://user:pass@products-database:5432/products", echo=True
)

seed(products_engine)
