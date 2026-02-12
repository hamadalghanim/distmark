from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetBuyerRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ...) -> None: ...

class GetBuyerResponse(_message.Message):
    __slots__ = ("success", "message", "buyer_id")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    BUYER_ID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    buyer_id: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., buyer_id: _Optional[int] = ...) -> None: ...

class BasicResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class CreateAccountRequest(_message.Message):
    __slots__ = ("name", "username", "password")
    NAME_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    name: str
    username: str
    password: str
    def __init__(self, name: _Optional[str] = ..., username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class CreateAccountResponse(_message.Message):
    __slots__ = ("success", "message", "buyer_id")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    BUYER_ID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    buyer_id: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., buyer_id: _Optional[int] = ...) -> None: ...

class LoginRequest(_message.Message):
    __slots__ = ("username", "password")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    username: str
    password: str
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class LoginResponse(_message.Message):
    __slots__ = ("success", "message", "session_id")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    session_id: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., session_id: _Optional[int] = ...) -> None: ...

class LogoutRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ...) -> None: ...

class AddItemToCartRequest(_message.Message):
    __slots__ = ("session_id", "item_id", "quantity")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    item_id: int
    quantity: int
    def __init__(self, session_id: _Optional[int] = ..., item_id: _Optional[int] = ..., quantity: _Optional[int] = ...) -> None: ...

class RemoveItemFromCartRequest(_message.Message):
    __slots__ = ("session_id", "item_id")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    item_id: int
    def __init__(self, session_id: _Optional[int] = ..., item_id: _Optional[int] = ...) -> None: ...

class ClearCartRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ...) -> None: ...

class SaveCartRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ...) -> None: ...

class CartItem(_message.Message):
    __slots__ = ("item_id", "quantity")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    item_id: int
    quantity: int
    def __init__(self, item_id: _Optional[int] = ..., quantity: _Optional[int] = ...) -> None: ...

class GetCartRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ...) -> None: ...

class GetCartResponse(_message.Message):
    __slots__ = ("success", "message", "session_cart", "saved_cart")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SESSION_CART_FIELD_NUMBER: _ClassVar[int]
    SAVED_CART_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    session_cart: _containers.RepeatedCompositeFieldContainer[CartItem]
    saved_cart: _containers.RepeatedCompositeFieldContainer[CartItem]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., session_cart: _Optional[_Iterable[_Union[CartItem, _Mapping]]] = ..., saved_cart: _Optional[_Iterable[_Union[CartItem, _Mapping]]] = ...) -> None: ...

class GetBuyerPurchasesRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ...) -> None: ...

class PurchaseItem(_message.Message):
    __slots__ = ("item_id", "quantity")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    item_id: int
    quantity: int
    def __init__(self, item_id: _Optional[int] = ..., quantity: _Optional[int] = ...) -> None: ...

class GetBuyerPurchasesResponse(_message.Message):
    __slots__ = ("success", "message", "purchases")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PURCHASES_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    purchases: _containers.RepeatedCompositeFieldContainer[PurchaseItem]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., purchases: _Optional[_Iterable[_Union[PurchaseItem, _Mapping]]] = ...) -> None: ...
