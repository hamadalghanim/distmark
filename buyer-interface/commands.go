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
	// add to local cart
	id, _ := strconv.Atoi(strings.TrimSpace(item_id))
	qty, _ := strconv.Atoi(strings.TrimSpace(quantity))
	LocalCart.AddToCart(id, qty)
	fmt.Println("Item added to local cart.")
	return ""
}

func RemoveItemFromCart(reader *bufio.Reader) string {
	fmt.Print("Item ID: ")
	item_id, _ := reader.ReadString('\n')
	fmt.Print("Quantity: ")
	quantity, _ := reader.ReadString('\n')
	// remove from local cart
	id, _ := strconv.Atoi(strings.TrimSpace(item_id))
	qty, _ := strconv.Atoi(strings.TrimSpace(quantity))
	LocalCart.RemoveFromCart(id, qty)
	fmt.Println("Item removed from local cart.")
	return ""
}

func DisplayCart() string {
	// display local cart
	if len(LocalCart) == 0 {
		fmt.Println("Local cart is empty.")
	} else {
		fmt.Println("Local Cart Contents:")
		for _, item := range LocalCart {
			fmt.Printf("Item ID: %d, Quantity: %d\n", item.ItemID, item.Quantity)
		}
	}
	fmt.Println("\nRemote Cart Contents:")
	return "getcart\n" + fmt.Sprintf("%d", SessionId) + "\n"
}

func SaveCart() string {
	// command session_id list of items and quantities
	if len(LocalCart) == 0 {
		fmt.Println("Local cart is empty. Nothing to save.")
		return ""
	}
	fmt.Println("Saving local cart to server...")

	return "SaveCart\n" + fmt.Sprintf("%d", SessionId) + "\n" + LocalCart.buildCartItemsString() + "\n"
}
func ClearCart() string {
	// clear local cart
	LocalCart.ClearCart()
	fmt.Println("Local cart cleared.")
	return ""
}
