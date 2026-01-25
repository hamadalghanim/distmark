package main

import (
	"bufio"
	"errors"
	"fmt"
	"net"
	"os"
	"regexp"
	"strconv"
	"strings"
)

func handle_command(command string, session_id int) (string, error) {

	reader := bufio.NewReader(os.Stdin)

	command = strings.TrimSpace(command)

	switch command {
	case "createaccount":
		return CreateAccount(reader), nil

	case "login":
		return Login(reader), nil
	case "logout":
		if session_id == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return Logout(session_id), nil
	case "getsellerrating":
		if session_id == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return GetSellerRating(session_id), nil
	case "registeritemforsale":
		return "", nil
	case "changeitemprice":
		return "", nil
	case "displayitemsforsale":
		return "", nil
	default:
		return "", errors.New("Not a real command")
	}

}

func main() {

	session_id := 0
	// Connect to the TCP server running on localhost at port 8080.
	// Ensure the server is running before executing this client code.
	conn, err := net.Dial("tcp", "localhost:8000")
	if err != nil {
		fmt.Println("Error connecting:", err.Error())
		os.Exit(1)
	}
	defer conn.Close() // Ensure the connection is closed when main function exits.

	fmt.Println("Connected to server at " + conn.RemoteAddr().String())

	fmt.Print("Available commands:\n" +
		"CreateAccount - SETS UP USERNAME+PASSWORD, RETURNS SELLER_ID\n" +
		"Login - LOGIN WITH USERNAME+PASSWORD (starts session)\n" +
		"Logout - ENDS ACTIVE SELLER SESSION\n" +
		"GetSellerRating - RETURNS FEEDBACK FOR CURRENT SELLER\n" +
		"RegisterItemForSale - REGISTER ITEM WITH ATTRIBUTES AND QUANTITY, RETURNS ITEM_ID\n" +
		"ChangeItemPrice - UPDATE ITEM PRICE BY ITEM_ID\n" +
		"UpdateUnitsForSale - REMOVE QUANTITY FROM ITEM_ID\n" +
		"DisplayItemsForSale - DISPLAY ITEMS ON SALE BY CURRENT SELLER\n")
	for {
		reader := bufio.NewReader(os.Stdin)
		fmt.Print("\nEnter command: ")
		command, _ := reader.ReadString('\n')
		command = strings.ToLower(command)

		message, error_handle := handle_command(command, session_id)
		if error_handle != nil {
			fmt.Println("Error handling command:", error_handle.Error())
			continue
		}
		_, err = conn.Write([]byte(message))
		if err != nil {
			fmt.Println("Error writing to server:", err.Error())
			return
		}

		// Buffer to read response from the server.
		buffer := make([]byte, 1024)
		n, err := conn.Read(buffer)
		if err != nil {
			fmt.Println("Error reading from server:", err.Error())
			return
		}
		if strings.TrimSpace(command) == "login" {
			// the buffer will have the session Id
			re := regexp.MustCompile("[0-9]+")
			match := re.Find(buffer[:n])
			if match != nil {
				id, err := strconv.Atoi(string(match))
				if err == nil {
					session_id = id
				} else {
					fmt.Println("Failed to parse session id:", err)
				}
			} else {
				fmt.Println("No session id found in server response")
			}
		}
		if strings.TrimSpace(command) == "Logout" && strings.TrimSpace(string(buffer[:n])) == "logout successful" {
			session_id = 0
		}
		if strings.TrimSpace(string(buffer[:n])) == "Session no longer valid" {
			session_id = 0
		}
		fmt.Printf(string(buffer[:n]))
	}
}
