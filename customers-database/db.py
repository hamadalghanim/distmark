from typing import List, Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String, INT, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from datetime import datetime, timezone


class BaseCustomers(DeclarativeBase):
    pass


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
    buyer_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("buyer_sessions.id"), nullable=True, default=None
    )
    session: Mapped[Optional["BuyerSession"]] = relationship(
        back_populates="cart", uselist=False
    )
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
