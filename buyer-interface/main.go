package main

import (
	"fmt"
	"os"
)

var serverURL = getEnv("SERVER_ADDRESS", "http://localhost:8001")

var SessionId int = 0

func main() {
	fmt.Println("Welcome to the Buyer Shopping System!")
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
		case "categories":
			GetCategoriesInteractive()
		case "search":
			SearchItemsInteractive()
		case "getitem":
			GetItemInteractive()
		case "addcart":
			AddToCartInteractive()
		case "removecart":
			RemoveFromCartInteractive()
		case "viewcart":
			DisplayCartInteractive()
		case "savecart":
			SaveCartInteractive()
		case "clearcart":
			ClearCartInteractive()
		case "purchase":
			MakePurchaseInteractive()
		case "history":
			ViewPurchaseHistoryInteractive()
		case "feedback":
			ProvideFeedbackInteractive()
		case "rating":
			GetSellerRatingInteractive()
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
