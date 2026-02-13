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
	BuyerID int `json:"buyer_id"`
}

type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type LoginResponse struct {
	BaseResponse
	SessionID int `json:"session_id"`
}

type LogoutRequest struct {
	SessionID int `json:"session_id"`
}

type SessionRequest struct {
	SessionID int `json:"session_id"`
}

//////////////////////////////////////////////////////
// Item Models
//////////////////////////////////////////////////////

type Item struct {
	ID         int     `json:"id"`
	Name       string  `json:"name"`
	CategoryID int     `json:"category_id"`
	Keywords   string  `json:"keywords"`
	Condition  string  `json:"condition"`
	SalePrice  float64 `json:"sale_price"`
	Quantity   int     `json:"quantity"`
	SellerID   int     `json:"seller_id"`
}

type ItemResponse struct {
	BaseResponse
	Item Item `json:"item"`
}

type ItemsResponse struct {
	BaseResponse
	Items []Item `json:"items"`
}

//////////////////////////////////////////////////////
// Category Models
//////////////////////////////////////////////////////

type Category struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

type CategoriesResponse struct {
	BaseResponse
	Categories []Category `json:"categories"`
}

//////////////////////////////////////////////////////
// Cart Models
//////////////////////////////////////////////////////

type CartItem struct {
	ItemID   int `json:"item_id"`
	Quantity int `json:"quantity"`
}

type CartItemRequest struct {
	ItemID    string `json:"item_id"`
	Quantity  string `json:"quantity"`
	SessionID int    `json:"session_id"`
}

type RemoveCartItemRequest struct {
	SessionID int    `json:"session_id"`
	ItemID    string `json:"item_id"`
}

type CartResponse struct {
	BaseResponse
	SessionCart []CartItem `json:"session_cart"`
	SavedCart   []CartItem `json:"saved_cart"`
}

//////////////////////////////////////////////////////
// Feedback Models
//////////////////////////////////////////////////////

type FeedbackRequest struct {
	ItemID    string `json:"item_id"`
	Feedback  string `json:"feedback"`
	SessionID int    `json:"session_id"`
}

type SellerRatingResponse struct {
	BaseResponse
	Feedback float64 `json:"feedback"`
}

// ////////////////////////////////////////////////////
// Purchase Models
// ////////////////////////////////////////////////////
type MakePurchaseRequest struct {
	SessionID      int    `json:"session_id"`
	CardNumber     string `json:"card_number"`
	ExpirationDate string `json:"expiration_date"`
	SecurityCode   string `json:"security_code"`
}

type PurchasesResponse struct {
	BaseResponse
	Purchases []CartItem `json:"purchases"`
}

//////////////////////////////////////////////////////
// Helper Functions
//////////////////////////////////////////////////////

func printItems(items []Item) {
	if len(items) == 0 {
		fmt.Println("No items found")
		return
	}

	fmt.Printf("%-5s %-30s %-10s %-10s %-8s %-10s\n", "ID", "Name", "Category", "Price", "Qty", "Seller")
	fmt.Println(strings.Repeat("─", 80))

	for _, item := range items {
		fmt.Printf("%-5d %-30s %-10d $%-9.2f %-8d %-10d\n",
			item.ID,
			truncate(item.Name, 30),
			item.CategoryID,
			item.SalePrice,
			item.Quantity,
			item.SellerID,
		)
	}
}

func printItem(item Item) {
	fmt.Println("\nItem Details")
	fmt.Println("------------")
	fmt.Printf("ID:         %d\n", item.ID)
	fmt.Printf("Name:       %s\n", item.Name)
	fmt.Printf("Category:   %d\n", item.CategoryID)
	fmt.Printf("Keywords:   %s\n", item.Keywords)
	fmt.Printf("Condition:  %s\n", item.Condition)
	fmt.Printf("Price:      $%.2f\n", item.SalePrice)
	fmt.Printf("Quantity:   %d\n", item.Quantity)
	fmt.Printf("Seller ID:  %d\n", item.SellerID)
}
