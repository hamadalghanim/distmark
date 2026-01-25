from sqlalchemy.orm import Session

from db import (
    BaseProducts,
    Item,
    Category,
    Seller,
    Session as SellerSession,
    Condition,
)
from datetime import datetime

# Create all tables


def seed(products_engine):
    BaseProducts.metadata.create_all(products_engine)

    # Create a session
    with Session(products_engine) as session:
        # Check if database is already seeded
        category_count = session.query(Category).count()
        seller_count = session.query(Seller).count()
        item_count = session.query(Item).count()

        if category_count > 0 or seller_count > 0 or item_count > 0:
            print("Database already contains data. Skipping seed.")
            print(
                f"Current counts - Categories: {category_count}, Sellers: {seller_count}, Items: {item_count}"
            )
            exit(0)

        print("Database is empty. Starting seed process...")

        # Create categories
        electronics = Category(name="Electronics")
        books = Category(name="Books")
        clothing = Category(name="Clothing")
        home = Category(name="Home & Garden")

        session.add_all([electronics, books, clothing, home])
        session.commit()

        # Create sellers
        seller = Seller(
            name="John Doe",
            username="johndoe",
            password="password123",
            feedback=95,
            items_sold=150,
        )

        session.add_all([seller])
        session.commit()

        # Create items
        items = [
            Item(
                name="Laptop",
                category_id=electronics.id,
                keywords="computer,portable,tech,work",
                condition=Condition.NEW,
                sale_price=899.99,
                quantity=5,
                feedback=10,
                seller_id=seller.id,
            ),
            Item(
                name="Smartphone",
                category_id=electronics.id,
                keywords="phone,mobile,tech,android",
                condition=Condition.USED,
                sale_price=299.99,
                quantity=3,
                feedback=8,
                seller_id=seller.id,
            ),
            Item(
                name="Python Programming",
                category_id=books.id,
                keywords="coding,learning,tech,guide",
                condition=Condition.NEW,
                sale_price=39.99,
                quantity=20,
                feedback=15,
                seller_id=seller.id,
            ),
        ]

        session.add_all(items)
        session.commit()

        # Create sessions for sellers
        sessions = [
            SellerSession(seller_id=seller.id, last_activity=datetime.utcnow()),
        ]

        session.add_all(sessions)
        session.commit()

        print("Database seeded successfully!")
        print(f"Created {len([electronics, books, clothing, home])} categories")
        print(f"Created {len([seller])} sellers")
        print(f"Created {len(items)} items")
        print(f"Created {len(sessions)} sessions")
