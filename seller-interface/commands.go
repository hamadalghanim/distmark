package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"net/url"
	"strconv"
	"strings"
)

func CreateAccount(reader *bufio.Reader) {
	fmt.Print("Name: ")
	name, _ := reader.ReadString('\n')

	fmt.Print("Username: ")
	username, _ := reader.ReadString('\n')

	fmt.Print("Password: ")
	password, _ := reader.ReadString('\n')

	req := RegisterRequest{
		Name:     strings.TrimSpace(name),
		Username: strings.TrimSpace(username),
		Password: strings.TrimSpace(password),
	}

	resp, err := sendPostRequest("/account/register", req)
	if err != nil {
		return
	}

	var result RegisterResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("Registered with seller %d\n", result.SellerID)
	} else {
		fmt.Println(result.Message)
	}
}

func Login(reader *bufio.Reader) {
	fmt.Print("Username: ")
	username, _ := reader.ReadString('\n')

	fmt.Print("Password: ")
	password, _ := reader.ReadString('\n')

	req := LoginRequest{
		Username: strings.TrimSpace(username),
		Password: strings.TrimSpace(password),
	}

	resp, err := sendPostRequest("/account/login", req)
	if err != nil {
		return
	}

	var result LoginResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		if result.SessionID != 0 {
			SessionId = result.SessionID
			fmt.Printf("Logged in with Session ID: %d\n", SessionId)
		}
	} else {
		fmt.Println(result.Message)
	}

}

func Logout(reader *bufio.Reader) {
	req := LogoutRequest{
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/account/logout", req)
	if err != nil {
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		SessionId = 0
		fmt.Println("Session cleared.")
	} else {
		fmt.Println(result.Message)
	}
}

func GetSellerRating(reader *bufio.Reader) {
	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	resp, err := sendGetRequest("/seller/rating", params)
	if err != nil {
		return
	}

	var result SellerRatingResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		sign := ""
		if result.Feedback > 0 {
			sign = "+"
		} else {
			sign = "-"
		}
		fmt.Printf("Seller rating: %s%d\n", sign, int(result.Feedback))

	} else {
		fmt.Println(result.Message)
	}
}

func RegisterItemForSale(reader *bufio.Reader) {
	fmt.Print("Item Name: ")
	name, _ := reader.ReadString('\n')

	fmt.Print("Category ID: ")
	category, _ := reader.ReadString('\n')

	fmt.Print("Price: ")
	price, _ := reader.ReadString('\n')

	fmt.Print("Quantity: ")
	qty, _ := reader.ReadString('\n')

	req := RegisterItemRequest{
		Name:      strings.TrimSpace(name),
		Category:  strings.TrimSpace(category),
		Price:     strings.TrimSpace(price),
		Qty:       strings.TrimSpace(qty),
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/items", req)
	if err != nil {
		return
	}

	var result RegisterItemResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("Item registered with ID: %d\n", result.ItemID)
	} else {
		fmt.Println(result.Message)
	}
}

func ChangeItemPrice(reader *bufio.Reader) {
	fmt.Print("Item ID: ")
	itemID, _ := reader.ReadString('\n')

	fmt.Print("New Price: ")
	newPrice, _ := reader.ReadString('\n')

	req := ChangePriceRequest{
		ItemID:    strings.TrimSpace(itemID),
		NewPrice:  strings.TrimSpace(newPrice),
		SessionID: SessionId,
	}

	resp, err := sendPutRequest("/items/price", req)
	if err != nil {
		return
	}

	var result ChangePriceResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("Price updated to %.2f\n", result.CurrentPrice)
	} else {
		fmt.Println(result.Message)
	}
}

func UpdateUnitsForSale(reader *bufio.Reader) {
	fmt.Print("Item ID: ")
	itemID, _ := reader.ReadString('\n')

	fmt.Print("New Quantity: ")
	newQty, _ := reader.ReadString('\n')

	req := ChangeQuantityRequest{
		ItemID:    strings.TrimSpace(itemID),
		NewQty:    strings.TrimSpace(newQty),
		SessionID: SessionId,
	}

	resp, err := sendPutRequest("/items/quantity", req)
	if err != nil {
		return
	}

	var result ChangeQuantityResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("Quantity updated to %d\n", result.CurrentQuantity)
	} else {
		fmt.Println(result.Message)
	}
}

func DisplayItemsForSale() {
	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	resp, err := sendGetRequest("/items", params)
	if err != nil {
		return
	}

	var result ItemsResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result != "success" {
		fmt.Println(result.Message)
		return
	}

	fmt.Println("Items For Sale")
	fmt.Println("--------------")

	printItems(result.Items)
}

func GetCategories() {
	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	resp, err := sendGetRequest("/categories", params)
	if err != nil {
		return
	}

	var result CategoriesResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result != "success" {
		fmt.Println(result.Message)
		return
	}

	fmt.Println("Categories")
	fmt.Println("----------")

	for _, c := range result.Categories {
		fmt.Printf("[%d] %s\n", c.ID, c.Name)
	}
}
