package main

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"strings"
)

func handle_command(command string) string {

	reader := bufio.NewReader(os.Stdin)
	message := ""

	command = strings.TrimSpace(command)

	switch command {
	case "CreateAccount":
		message = CreateAccount(reader)
	case "Login":

	case "Logout":
	case "GetSellerRating":
	case "RegisterItemForSale":
	case "ChangeItemPrice":
	case "DisplayItemsForSale":
	default:
		message = "Unknown Command"
	}

	return message
}

func main() {
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
		message := ""
		message = handle_command(command)

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

		fmt.Printf(string(buffer[:n]))
	}
}
