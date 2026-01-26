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
func Logout(session_id int) string {
	return "Logout\n" + fmt.Sprintf("%d", session_id) + "\n"
}

func GetSellerRating(session_id int) string {
	return "GetSellerRating\n" + fmt.Sprintf("%d", session_id) + "\n"
}

func GetCategories(session_id int) string {
	return "GetCategories\n" + fmt.Sprintf("%d", session_id) + "\n"
}

func RegisterItemForSale(session_id int, reader *bufio.Reader) string {
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

	return "RegisterItemForSale\n" + fmt.Sprintf("%d", session_id) + "\n" + item_name + "\n" + category_id + "\n" + keywords + "\n" + condition + "\n" + price + "\n" + quantity + "\n"
}

func buildKeywords(reader *bufio.Reader) string {
	kws := []string{}
	const maxKeywords = 5
	const maxKeywordLen = 8

	for i := 0; i < maxKeywords; i++ {
		fmt.Printf("Keyword #%d: ", i+1)
		k, err := reader.ReadString('\n')
		if err != nil {
			fmt.Println("Error reading keyword:", err)

			return ""
		}

		k = strings.TrimSpace(k)
		if k == "" {
			break
		}

		if len(k) > maxKeywordLen {
			k = k[:maxKeywordLen]
		}
		kws = append(kws, k)
	}

	keywords := strings.Join(kws, ",")
	return keywords
}
func ChangeItemPrice(session_id int, reader *bufio.Reader) string {
	// Structure "command name", "session_id","item id","new price"
	fmt.Print("Item ID: ")
	item_id, _ := reader.ReadString('\n')
	fmt.Print("New Price: ")
	new_price, _ := reader.ReadString('\n')

	return "ChangeItemPrice\n" + fmt.Sprintf("%d", session_id) + "\n" + item_id + "\n" + new_price + "\n"
}
func UpdateUnitsForSale(session_id int, reader *bufio.Reader) string {
	// Structure "command name", "session_id","item id","new quantity"
	fmt.Print("Item ID: ")
	item_id, _ := reader.ReadString('\n')
	fmt.Print("New Quantity: ")
	new_quantity, _ := reader.ReadString('\n')

	return "UpdateUnitsForSale\n" + fmt.Sprintf("%d", session_id) + "\n" + item_id + "\n" + new_quantity + "\n"
}
func DisplayItemsForSale(session_id int) string {
	return "DisplayItemsForSale\n" + fmt.Sprintf("%d", session_id) + "\n"
}
