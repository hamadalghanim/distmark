package main

import (
	"fmt"
	"strings"
)

////////////////////////////////////////////////////
// Shared Response Models
//////////////////////////////////////////////////////

type BaseResponse struct {
	Result  string `json:"result"`
	Message string `json:"message"`
}

//////////////////////////////////////////////////////
// Account Models
//////////////////////////////////////////////////////

type RegisterRequest struct {
	Name     string `json:"name"`
	Username string `json:"username"`
	Password string `json:"password"`
}

type RegisterResponse struct {
	BaseResponse
	SellerID int `json:"seller_id"`
}

type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type LoginResponse struct {
	SessionID int `json:"session_id"`
}

type LogoutRequest struct {
	SessionID int `json:"session_id"`
}

type SellerRatingResponse struct {
	BaseResponse
	Feedback float64 `json:"feedback"`
}

func printItems(items []Item) {
	fmt.Printf("%-5s %-30s %-10s %-10s %-8s\n", "ID", "Name", "Category", "Price", "Qty")
	fmt.Println(strings.Repeat("─", 70))

	for _, item := range items {
		fmt.Printf("%-5d %-30s %-10d $%-9.2f %-8d\n",
			item.ID,
			truncate(item.Name, 30),
			item.CategoryID,
			item.SalePrice,
			item.Quantity,
		)
	}
}

type Item struct {
	ID         int     `json:"id"`
	Name       string  `json:"name"`
	CategoryID int     `json:"category_id"`
	Keywords   string  `json:"keywords"`
	Condition  string  `json:"condition"`
	SalePrice  float64 `json:"sale_price"`
	Quantity   int     `json:"quantity"`
}

type ItemsResponse struct {
	BaseResponse
	Items []Item `json:"items"`
}

type RegisterItemRequest struct {
	Name      string `json:"name"`
	Category  string `json:"category"`
	Price     string `json:"price"`
	Qty       string `json:"qty"`
	SessionID int    `json:"session_id"`
}

type RegisterItemResponse struct {
	BaseResponse
	ItemID int `json:"item_id"`
}

type ChangePriceRequest struct {
	ItemID    string `json:"item_id"`
	NewPrice  string `json:"new_price"`
	SessionID int    `json:"session_id"`
}

type ChangePriceResponse struct {
	BaseResponse
	CurrentPrice float64 `json:"current_price"`
}

type ChangeQuantityRequest struct {
	ItemID    string `json:"item_id"`
	NewQty    string `json:"new_qty"`
	SessionID int    `json:"session_id"`
}

type ChangeQuantityResponse struct {
	BaseResponse
	CurrentQuantity int `json:"current_quantity"`
}

type Category struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

type CategoriesResponse struct {
	BaseResponse
	Categories []Category `json:"categories"`
}
