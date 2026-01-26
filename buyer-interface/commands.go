package main

import (
	"bufio"
	"fmt"
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

func RegisterItemForSale(reader *bufio.Reader) string {
	// Structure "command name", "session_id","item name","category_id", "Keywords", "condition", "price", "qty"
	fmt.Print("Item Name: ")
	item_name, _ := reader.ReadString('\n')
	fmt.Print("Category ID: ")
	category_id, _ := reader.ReadString('\n')
	fmt.Print("Keywords (enter one at a time, empty to finish, max 5, max 8 chars each):\n")
	keywords := buildKeywords(reader)
	fmt.Print("Condition (new, used): ")
	condition, _ := reader.ReadString('\n')
	fmt.Print("Price: ")
	price, _ := reader.ReadString('\n')
	fmt.Print("Quantity: ")
	quantity, _ := reader.ReadString('\n')

	return "RegisterItemForSale\n" + fmt.Sprintf("%d", SessionId) + "\n" + item_name + "\n" + category_id + "\n" + keywords + "\n" + condition + "\n" + price + "\n" + quantity + "\n"
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
