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
		fmt.Printf("Registered with buyer %d\n", result.BuyerID)
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

func GetItem(reader *bufio.Reader) {
	fmt.Print("Item ID: ")
	itemID, _ := reader.ReadString('\n')

	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	endpoint := fmt.Sprintf("/items/%s", strings.TrimSpace(itemID))
	resp, err := sendGetRequest(endpoint, params)
	if err != nil {
		return
	}

	var result ItemResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		printItem(result.Item)
	} else {
		fmt.Println(result.Message)
	}
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

func SearchItemsForSale(reader *bufio.Reader) {
	fmt.Print("Category ID (0 for all): ")
	category, _ := reader.ReadString('\n')

	fmt.Print("Keywords (comma-separated, optional): ")
	keywords := buildKeywords(reader)

	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))
	params.Add("category", strings.TrimSpace(category))
	if strings.TrimSpace(keywords) != "" {
		params.Add("keywords", strings.TrimSpace(keywords))
	}

	resp, err := sendGetRequest("/items/search", params)
	if err != nil {
		return
	}

	var result ItemsResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result != "success" {
		fmt.Println(result.Message)
		return
	}

	fmt.Println("Search Results")
	fmt.Println("--------------")

	printItems(result.Items)
}

func AddItemToCart(reader *bufio.Reader) {
	fmt.Print("Item ID: ")
	itemID, _ := reader.ReadString('\n')

	fmt.Print("Quantity: ")
	quantity, _ := reader.ReadString('\n')

	req := CartItemRequest{
		ItemID:    strings.TrimSpace(itemID),
		Quantity:  strings.TrimSpace(quantity),
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/cart/items", req)
	if err != nil {
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Println(result.Message)
	} else {
		fmt.Println(result.Message)
	}
}

func RemoveItemFromCart(reader *bufio.Reader) {
	fmt.Print("Item ID: ")
	itemID, _ := reader.ReadString('\n')

	req := RemoveCartItemRequest{
		SessionID: SessionId,
		ItemID:    strings.TrimSpace(itemID),
	}

	endpoint := fmt.Sprintf("/cart/items/%s", strings.TrimSpace(itemID))
	resp, err := sendDeleteRequest(endpoint, req)
	if err != nil {
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Println(result.Message)
	} else {
		fmt.Println(result.Message)
	}
}

func DisplayCart() {
	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	resp, err := sendGetRequest("/cart", params)
	if err != nil {
		return
	}

	var result CartResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result != "success" {
		fmt.Println(result.Message)
		return
	}

	fmt.Println("Shopping Cart")
	fmt.Println("=============")

	if len(result.SessionCart) > 0 {
		fmt.Println("\nSession Cart:")
		for _, item := range result.SessionCart {
			fmt.Printf("  Item ID: %d, Quantity: %d\n", item.ItemID, item.Quantity)
		}
	} else {
		fmt.Println("\nSession Cart: Empty")
	}

	if len(result.SavedCart) > 0 {
		fmt.Println("\nSaved Cart:")
		for _, item := range result.SavedCart {
			fmt.Printf("  Item ID: %d, Quantity: %d\n", item.ItemID, item.Quantity)
		}
	}
}

func SaveCart() {
	req := SessionRequest{
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/cart/save", req)
	if err != nil {
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Println(result.Message)
	} else {
		fmt.Println(result.Message)
	}
}

func ClearCart() {
	req := SessionRequest{
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/cart/clear", req)
	if err != nil {
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Println(result.Message)
	} else {
		fmt.Println(result.Message)
	}
}

func ProvideFeedback(reader *bufio.Reader) {
	fmt.Print("Item ID: ")
	itemID, _ := reader.ReadString('\n')

	fmt.Print("Feedback (up/down): ")
	feedback, _ := reader.ReadString('\n')
	feedback = strings.ToLower(strings.TrimSpace(feedback))

	if feedback != "up" && feedback != "down" {
		fmt.Println("Invalid feedback. Please enter 'up' or 'down'.")
		return
	}

	feedbackValue := "1"
	if feedback == "down" {
		feedbackValue = "-1"
	}

	req := FeedbackRequest{
		ItemID:    strings.TrimSpace(itemID),
		Feedback:  feedbackValue,
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/feedback", req)
	if err != nil {
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Println(result.Message)
	} else {
		fmt.Println(result.Message)
	}
}

func GetSellerRating(reader *bufio.Reader) {
	fmt.Print("Seller ID: ")
	sellerID, _ := reader.ReadString('\n')

	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	endpoint := fmt.Sprintf("/seller/%s/rating", strings.TrimSpace(sellerID))
	resp, err := sendGetRequest(endpoint, params)
	if err != nil {
		return
	}

	var result SellerRatingResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("Seller rating: %f\n", result.Feedback)
	} else {
		fmt.Println(result.Message)
	}
}

func GetBuyerPurchases() {
	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	resp, err := sendGetRequest("/purchases", params)
	if err != nil {
		return
	}

	var result PurchasesResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result != "success" {
		fmt.Println(result.Message)
		return
	}

	if len(result.Purchases) == 0 {
		fmt.Println("No purchases found")
		return
	}

	fmt.Println("Purchase History")
	fmt.Println("----------------")
	for _, item := range result.Purchases {
		fmt.Printf("Item ID: %d, Quantity: %d\n", item.ItemID, item.Quantity)
	}
}

func MakePurchase() {
	req := SessionRequest{
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/purchase", req)
	if err != nil {
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Println(result.Message)
	} else {
		fmt.Println(result.Message)
	}
}
