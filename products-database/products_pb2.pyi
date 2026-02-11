from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Item(_message.Message):
    __slots__ = ("id", "name", "category_id", "keywords", "condition", "sale_price", "quantity", "seller_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_ID_FIELD_NUMBER: _ClassVar[int]
    KEYWORDS_FIELD_NUMBER: _ClassVar[int]
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    SALE_PRICE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    SELLER_ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    category_id: int
    keywords: str
    condition: str
    sale_price: float
    quantity: int
    seller_id: int
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., category_id: _Optional[int] = ..., keywords: _Optional[str] = ..., condition: _Optional[str] = ..., sale_price: _Optional[float] = ..., quantity: _Optional[int] = ..., seller_id: _Optional[int] = ...) -> None: ...

class Category(_message.Message):
    __slots__ = ("id", "name", "description")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    description: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

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
    __slots__ = ("success", "message", "seller_id")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SELLER_ID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    seller_id: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., seller_id: _Optional[int] = ...) -> None: ...

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

class LogoutResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class GetSellerRatingRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ...) -> None: ...

class RatingResponse(_message.Message):
    __slots__ = ("success", "message", "feedback")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FEEDBACK_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    feedback: float
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., feedback: _Optional[float] = ...) -> None: ...

class RegisterItemRequest(_message.Message):
    __slots__ = ("session_id", "item_name", "category_id", "keywords", "condition", "price", "quantity")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_NAME_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_ID_FIELD_NUMBER: _ClassVar[int]
    KEYWORDS_FIELD_NUMBER: _ClassVar[int]
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    item_name: str
    category_id: int
    keywords: str
    condition: str
    price: float
    quantity: int
    def __init__(self, session_id: _Optional[int] = ..., item_name: _Optional[str] = ..., category_id: _Optional[int] = ..., keywords: _Optional[str] = ..., condition: _Optional[str] = ..., price: _Optional[float] = ..., quantity: _Optional[int] = ...) -> None: ...

class RegisterItemResponse(_message.Message):
    __slots__ = ("success", "message", "item_id")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    item_id: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., item_id: _Optional[int] = ...) -> None: ...

class ChangeItemPriceRequest(_message.Message):
    __slots__ = ("session_id", "item_id", "new_price")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_PRICE_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    item_id: int
    new_price: float
    def __init__(self, session_id: _Optional[int] = ..., item_id: _Optional[int] = ..., new_price: _Optional[float] = ...) -> None: ...

class ChangeItemPriceResponse(_message.Message):
    __slots__ = ("success", "message", "current_price")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PRICE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    current_price: float
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., current_price: _Optional[float] = ...) -> None: ...

class UpdateUnitsRequest(_message.Message):
    __slots__ = ("session_id", "item_id", "new_quantity")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_QUANTITY_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    item_id: int
    new_quantity: int
    def __init__(self, session_id: _Optional[int] = ..., item_id: _Optional[int] = ..., new_quantity: _Optional[int] = ...) -> None: ...

class UpdateUnitsResponse(_message.Message):
    __slots__ = ("success", "message", "current_quantity")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_QUANTITY_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    current_quantity: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., current_quantity: _Optional[int] = ...) -> None: ...

class DisplayItemsRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ...) -> None: ...

class ItemListResponse(_message.Message):
    __slots__ = ("success", "message", "items")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    items: _containers.RepeatedCompositeFieldContainer[Item]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ...) -> None: ...

class GetCategoriesRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ...) -> None: ...

class CategoryListResponse(_message.Message):
    __slots__ = ("success", "message", "categories")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CATEGORIES_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    categories: _containers.RepeatedCompositeFieldContainer[Category]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., categories: _Optional[_Iterable[_Union[Category, _Mapping]]] = ...) -> None: ...
