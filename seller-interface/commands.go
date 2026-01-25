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
func Logout(session_id int) string {
	return "Logout\n" + fmt.Sprintf("%d", session_id) + "\n"
}

func GetSellerRating(session_id int) string {
	return "GetSellerRating\n" + fmt.Sprintf("%d", session_id) + "\n"
}
