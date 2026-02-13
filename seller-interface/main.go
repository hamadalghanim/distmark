package main

import (
	"fmt"
	"os"
)

var serverURL = getEnv("SERVER_ADDRESS", "http://localhost:8000")

var SessionId int = 0

func main() {
	fmt.Println("Welcome to the Seller Management System!")
	fmt.Println()

	for {
		choice := ShowInteractiveMenu()

		if choice == "" {
			break
		}

		fmt.Println() // Add spacing before command output

		switch choice {
		case "createaccount":
			CreateAccountInteractive()
		case "login":
			LoginInteractive()
		case "logout":
			LogoutInteractive()
		case "rating":
			GetSellerRatingInteractive()
		case "categories":
			GetCategoriesInteractive()
		case "sell":
			RegisterItemForSaleInteractive()
		case "changeprice":
			ChangeItemPriceInteractive()
		case "updateqty":
			UpdateUnitsForSaleInteractive()
		case "list":
			DisplayItemsForSaleInteractive()
		case "exit":
			fmt.Println("Goodbye!")
			os.Exit(0)
		default:
			fmt.Printf("Unknown command: %s\n", choice)
		}

		fmt.Println("\nPress Enter to continue...")
		fmt.Scanln() // Wait for user input before showing menu again
	}
}
