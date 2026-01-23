
from db import DatabaseConnection
customer_db = DatabaseConnection(
    db_name='customers',
    user='user',
    password='pass',
    host='customers-database',  # Updated to connect to the correct database service
    port=5432
)
customer_db.connect()

products_db = DatabaseConnection(
    db_name='products',
    user='user',
    password='pass',
    host='products-database',  # Updated to connect to the correct database service
    port=5432
)
products_db.connect()