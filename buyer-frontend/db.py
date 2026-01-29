from typing import List
from sqlalchemy import ForeignKey
from sqlalchemy import String, DECIMAL, INT, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from enum import Enum
from sqlalchemy import Enum as SQLEnum
from datetime import datetime, timezone


class BaseProducts(DeclarativeBase):
    pass


class Condition(Enum):
    NEW = "new"
    USED = "used"


class Item(BaseProducts):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship(back_populates="items")
    keywords: Mapped[str] = mapped_column(
        String(45)
    )  # 8 characters per word, 5 words + commas
    condition: Mapped[Condition] = mapped_column(
        SQLEnum(
            Condition,
            name="condition_enum",
            validate_strings=True,
        ),
        default=Condition.NEW,
        nullable=False,
    )
    seller_id: Mapped[int] = mapped_column(ForeignKey("sellers.id"))
    seller: Mapped["Seller"] = relationship(back_populates="items")

    sale_price: Mapped[float] = mapped_column(DECIMAL)
    quantity: Mapped[int] = mapped_column(INT)
    feedback: Mapped[int] = mapped_column(INT, default=0)

    def __repr__(self) -> str:
        return f"Item(id={self.id!r}, name={self.name!r}, category={self.category.name!r}, keywords={self.keywords!r}, condition={self.condition.name!r}, sale_price={self.sale_price}, quantity={self.quantity!r})"


class Category(BaseProducts):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32))

    items: Mapped[List["Item"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Category(id={self.id!r}, name={self.name!r})"


class Seller(BaseProducts):
    __tablename__ = "sellers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    username: Mapped[str] = mapped_column(String(32), unique=True)
    password: Mapped[str] = mapped_column(String(32))
    feedback: Mapped[int] = mapped_column(INT, default=0)
    items_sold: Mapped[int] = mapped_column(INT, default=0)
    items: Mapped[List["Item"]] = relationship(
        back_populates="seller", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["Session"]] = relationship(
        back_populates="seller", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Seller(id={self.id!r}, username={self.username!r})"


class Session(BaseProducts):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("sellers.id"))
    seller: Mapped["Seller"] = relationship(back_populates="sessions")
    last_activity: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(tz=timezone.utc),
        onupdate=datetime.now(tz=timezone.utc),
    )

    def __repr__(self) -> str:
        return f"Session(id={self.id!r}, seller_id={self.seller_id!r}, last_activity={self.last_activity!r})"


class BaseCustomers(DeclarativeBase):
    pass


"""
Buyer attributes
● Buyer name: a char string of up to 32 characters, provided by the buyer during
account creation (Buyer names may not be unique).
● Buyer ID: an integer, a unique id provided by the server during account creation.
● Number of items purchased: an integer maintained by the server. New buyers
should start with 0 items purchased.
"""


class Buyer(BaseCustomers):
    __tablename__ = "buyers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    username: Mapped[str] = mapped_column(String(32), unique=True)
    password: Mapped[str] = mapped_column(String(32))
    items_purchased: Mapped[int] = mapped_column(INT, default=0)
    carts: Mapped[List["Cart"]] = relationship(
        back_populates="buyer", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["BuyerSession"]] = relationship(
        back_populates="buyer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Buyer(id={self.id!r}, name={self.name!r}, items_purchased={self.items_purchased!r})"


class Cart(BaseCustomers):
    __tablename__ = "carts"
    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"))
    buyer: Mapped["Buyer"] = relationship(back_populates="carts")
    items: Mapped[List["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )
    buyer_session_id: Mapped[int] = mapped_column(ForeignKey("buyer_sessions.id"))
    session: Mapped["BuyerSession"] = relationship(back_populates="cart")
    saved: Mapped[bool] = mapped_column(default=False)

    def __repr__(self) -> str:
        return f"Cart(id={self.id!r}, buyer_id={self.buyer_id!r})"


class CartItem(BaseCustomers):
    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"))
    cart: Mapped["Cart"] = relationship(back_populates="items")
    item_id: Mapped[int] = mapped_column(INT)
    quantity: Mapped[int] = mapped_column(INT)

    def __repr__(self) -> str:
        return f"CartItem(id={self.id!r}, cart_id={self.cart_id!r}, item_id={self.item_id!r}, quantity={self.quantity!r})"


class ItemsBought(BaseCustomers):
    __tablename__ = "items_bought"
    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"))
    item_id: Mapped[int] = mapped_column(INT)
    quantity: Mapped[int] = mapped_column(INT)

    def __repr__(self) -> str:
        return f"ItemsBought(id={self.id!r}, buyer_id={self.buyer_id!r}, item_id={self.item_id!r}, quantity={self.quantity!r})"


class BuyerSession(BaseCustomers):
    __tablename__ = "buyer_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"))
    buyer: Mapped["Buyer"] = relationship(back_populates="sessions")
    cart: Mapped["Cart"] = relationship(
        back_populates="session", uselist=False, cascade="all, delete-orphan"
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(tz=timezone.utc),
        onupdate=datetime.now(tz=timezone.utc),
    )

    def __repr__(self) -> str:
        return f"BuyerSession(id={self.id!r}, buyer_id={self.buyer_id!r}, last_activity={self.last_activity!r})"
