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

func SearchItemsForSale(reader *bufio.Reader) string {
	// enter category id and keywords
	fmt.Print("Category ID (0 for all): ")
	category_id, _ := reader.ReadString('\n')
	fmt.Print("Keywords (enter one at a time, empty to finish, max 5, max 8 chars each):\n")
	keywords := buildKeywords(reader)

	return "SearchItemsForSale\n" + fmt.Sprintf("%d", SessionId) + "\n" + category_id + "\n" + keywords + "\n"
}
