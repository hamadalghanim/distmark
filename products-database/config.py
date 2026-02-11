from sqlalchemy import create_engine
from seed import seed

products_engine = create_engine(
    "postgresql+psycopg2://user:pass@products-database:5432/products",
    pool_size=20,
    max_overflow=0,
)
