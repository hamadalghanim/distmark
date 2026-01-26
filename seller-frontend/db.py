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
        return f"Item(id={self.id!r}, name={self.name!r}, category={self.category!r}, keywords={self.keywords!r}, condition={self.condition!r}, sale_price={self.sale_price!r}, quantity={self.quantity!r})"


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
