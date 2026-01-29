package main

import (
	"bufio"
	"fmt"
	"strings"
)

func CreateAccount(reader *bufio.Reader) string {
	fmt.Print("Name: ")
	name, _ := reader.ReadString('\n')
	fmt.Print("Username: ")
	username, _ := reader.ReadString('\n')
	fmt.Print("Password: ")
	password, _ := reader.ReadString('\n')
	return "CreateAccount\n" + name + "\n" + username + "\n" + password + "\n"
}
func Login(reader *bufio.Reader) string {
	fmt.Print("Username: ")
	username, _ := reader.ReadString('\n')
	fmt.Print("Password: ")
	password, _ := reader.ReadString('\n')
	return "Login\n" + username + "\n" + password + "\n"
}
func Logout() string {

	return "Logout\n" + fmt.Sprintf("%d", SessionId) + "\n"
}

func GetItem(reader *bufio.Reader) string {
	fmt.Print("Item ID: ")
	item_id, _ := reader.ReadString('\n')
	return "GetItem\n" + fmt.Sprintf("%d", SessionId) + "\n" + item_id + "\n"
}

func GetCategories() string {
	return "GetCategories\n" + fmt.Sprintf("%d", SessionId) + "\n"
}

func SearchItemsForSale(reader *bufio.Reader) string {
	// enter category id and keywords
	fmt.Print("Category ID (0 for all): ")
	category_id, _ := reader.ReadString('\n')
	fmt.Print("Keywords (enter one at a time, empty to finish, max 5, max 8 chars each):\n")
	keywords := buildKeywords(reader)

	return "SearchItemsForSale\n" + fmt.Sprintf("%d", SessionId) + "\n" + category_id + "\n" + keywords + "\n"
}

func AddItemToCart(reader *bufio.Reader) string {
	// Structure "command name", "session_id","item id","quantity"
	fmt.Print("Item ID: ")
	item_id, _ := reader.ReadString('\n')
	fmt.Print("Quantity: ")
	quantity, _ := reader.ReadString('\n')
	return "AddItemToCart\n" + fmt.Sprintf("%d", SessionId) + "\n" + item_id + "\n" + quantity + "\n"
}

func RemoveItemFromCart(reader *bufio.Reader) string {
	fmt.Print("Item ID: ")
	item_id, _ := reader.ReadString('\n')
	fmt.Print("Quantity: ")
	quantity, _ := reader.ReadString('\n')
	return "RemoveItemFromCart\n" + fmt.Sprintf("%d", SessionId) + "\n" + item_id + "\n" + quantity + "\n"
}

func DisplayCart() string {
	return "getcart\n" + fmt.Sprintf("%d", SessionId) + "\n"
}

func SaveCart() string {
	return "SaveCart\n" + fmt.Sprintf("%d", SessionId) + "\n"
}
func ClearCart() string {
	return "ClearCart\n" + fmt.Sprintf("%d", SessionId) + "\n"
}
func ProvideFeedback(reader *bufio.Reader) string {
	fmt.Print("Item ID: ")
	itemID, _ := reader.ReadString('\n')
	fmt.Print("Feedback (up/down): ")
	feedback, _ := reader.ReadString('\n')
	feedback = strings.ToLower(strings.TrimSpace(feedback))
	if feedback != "up" && feedback != "down" {
		fmt.Println("Invalid feedback. Please enter 'up' or 'down'.")
		return ""
	}
	if feedback == "up" {
		feedback = "1"
	} else {
		feedback = "-1"
	}
	return "ProvideFeedback\n" + fmt.Sprintf("%d", SessionId) + "\n" + itemID + "\n" + feedback + "\n"
}
func GetSellerRating(reader *bufio.Reader) string {
	fmt.Print("Seller ID: ")
	sellerID, _ := reader.ReadString('\n')
	return "GetSellerRating\n" + fmt.Sprintf("%d", SessionId) + "\n" + sellerID + "\n"
}
func GetBuyerPurchases() string {
	return "GetBuyerPurchases\n" + fmt.Sprintf("%d", SessionId) + "\n"
}
func MakePurchase() string {
	return "MakePurchase\n" + fmt.Sprintf("%d", SessionId) + "\n"
}
