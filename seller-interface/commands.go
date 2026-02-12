package main

import (
	"bufio"
	"fmt"
	"strconv"
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

func GetSellerRating() string {
	return "GetSellerRating\n" + fmt.Sprintf("%d", SessionId) + "\n"
}

func GetCategories() string {
	return "GetCategories\n" + fmt.Sprintf("%d", SessionId) + "\n"
}

func RegisterItemForSale(reader *bufio.Reader) string {
	// Structure "command name", "session_id","item name","category_id", "Keywords", "condition", "price", "qty"
	// --- 1. Item Name (Must not be empty) ---
	var itemName string
	for {
		fmt.Print("Item Name: ")
		input, _ := reader.ReadString('\n')
		itemName = strings.TrimSpace(input)
		if itemName != "" {
			break
		}
		fmt.Println("Error: Item name cannot be empty.")
	}

	// --- 2. Category ID (Must be an integer) ---
	var categoryID int
	for {
		fmt.Print("Category ID: ")
		input, _ := reader.ReadString('\n')
		var err error
		categoryID, err = strconv.Atoi(strings.TrimSpace(input))
		if err == nil {
			break
		}
		fmt.Println("Error: Category ID must be a valid number.")
	}

	// --- 3. Keywords (Max 5 items, Max 8 chars each) ---
	fmt.Print("Keywords (enter one at a time, empty to finish, max 5, max 8 chars each):\n")
	keywords := buildKeywords(reader)

	// --- 4. Condition (Must be 'new' or 'used') ---
	var condition string
	for {
		fmt.Print("Condition (new, used): ")
		input, _ := reader.ReadString('\n')
		condition = strings.ToLower(strings.TrimSpace(input))
		if condition == "new" || condition == "used" {
			break
		}
		fmt.Println("Error: Condition must be exactly 'new' or 'used'.")
	}

	// --- 5. Price (Must be a float and greater than 0) ---
	var price float64
	for {
		fmt.Print("Price: ")
		input, _ := reader.ReadString('\n')
		var err error
		price, err = strconv.ParseFloat(strings.TrimSpace(input), 64)
		if err == nil && price > 0 {
			break
		}
		fmt.Println("Error: Price must be a positive number.")
	}

	// --- 6. Quantity (Must be an integer and greater than 0) ---
	var quantity int
	for {
		fmt.Print("Quantity: ")
		input, _ := reader.ReadString('\n')
		var err error
		quantity, err = strconv.Atoi(strings.TrimSpace(input))
		if err == nil && quantity > 0 {
			break
		}
		fmt.Println("Error: Quantity must be a positive integer.")
	}

	// Construct string. Note: We use Sprintf for numbers to convert them back to string safely.
	// We manually re-add the newlines ("\n") because we trimmed them off the inputs earlier.
	return "RegisterItemForSale\n" +
		fmt.Sprintf("%d", SessionId) + "\n" +
		itemName + "\n" +
		fmt.Sprintf("%d", categoryID) + "\n" +
		keywords + "\n" +
		condition + "\n" +
		fmt.Sprintf("%.2f", price) + "\n" +
		fmt.Sprintf("%d", quantity) + "\n"
}

func ChangeItemPrice(reader *bufio.Reader) string {
	// Structure "command name", "session_id","item id","new price"
	fmt.Print("Item ID: ")
	item_id, _ := reader.ReadString('\n')
	fmt.Print("New Price: ")
	new_price, _ := reader.ReadString('\n')

	return "ChangeItemPrice\n" + fmt.Sprintf("%d", SessionId) + "\n" + item_id + "\n" + new_price + "\n"
}
func UpdateUnitsForSale(reader *bufio.Reader) string {
	// Structure "command name", "session_id","item id","new quantity"
	fmt.Print("Item ID: ")
	item_id, _ := reader.ReadString('\n')
	fmt.Print("New Quantity: ")
	new_quantity, _ := reader.ReadString('\n')

	return "UpdateUnitsForSale\n" + fmt.Sprintf("%d", SessionId) + "\n" + item_id + "\n" + new_quantity + "\n"
}
func DisplayItemsForSale() string {
	return "DisplayItemsForSale\n" + fmt.Sprintf("%d", SessionId) + "\n"
}
