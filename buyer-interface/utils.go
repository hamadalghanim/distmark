package main

import (
	"bufio"
	"errors"
	"fmt"
	"net"
	"os"
	"strings"
	"time"
)

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

func connectWithRetry(address string) (net.Conn, error) {
	const (
		maxReconnectAttempts = 3
		reconnectDelay       = 2 * time.Second
	)

	for attempt := 1; attempt <= maxReconnectAttempts; attempt++ {
		conn, err := net.Dial("tcp", address)
		if err == nil {
			return conn, nil
		}

		if attempt < maxReconnectAttempts {
			fmt.Printf("Connection failed (attempt %d/%d), retrying in %v...\n",
				attempt, maxReconnectAttempts, reconnectDelay)
			time.Sleep(reconnectDelay)
		}
	}
	return nil, fmt.Errorf("failed to connect after %d attempts", maxReconnectAttempts)
}

func print_menu() {
	fmt.Print("Available commands:\n" +
		"1. \033[1mCreateAccount\033[0m - Sets up username and password, returns seller ID\n" +
		"2. \033[1mLogin\033[0m - Login with username and password (starts session)\n" +
		"3. \033[1mLogout\033[0m - Ends active seller session\n" +
		"4. \033[1mGetItem\033[0m - Returns Item details\n" +
		"5. \033[1mGetCategories\033[0m - Get a list of categories\n" +
		"6. \033[1mSearchItemsForSale\033[0m - Search items for sale by keywords\n" +
		"7. \033[1mAddItemToCart\033[0m - Add item to shopping cart\n" +
		"8. \033[1mRemoveItemFromCart\033[0m - Remove item from shopping cart\n" +
		"9. \033[1mDisplayCart\033[0m - Display items in shopping cart\n" +
		"10. \033[1mSaveCart\033[0m - Save the shopping cart\n" +
		"11. \033[1mClearCart\033[0m - Clear the shopping cart\n" +
		"12. \033[1mExit\033[0m or \033[1mQuit\033[0m - Exit the application\n" +
		"14. \033[1mHelp\033[0m - Show this menu\n")
}

func dispatch_command(command string) (string, error) {

	reader := bufio.NewReader(os.Stdin)

	command = strings.TrimSpace(command)

	switch command {
	case "createaccount", "register", "1":
		return CreateAccount(reader), nil

	case "login", "2":
		return Login(reader), nil
	case "logout", "3":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return Logout(), nil
	case "getitem", "4":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return GetItem(reader), nil
	case "getcategories", "5":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return GetCategories(), nil
	case "searchitemsforsale", "6":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return SearchItemsForSale(reader), nil
	case "additemtocart", "7":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return AddItemToCart(reader), nil
	case "removeitemfromcart", "8":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return RemoveItemFromCart(reader), nil
	case "displaycart", "9":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return DisplayCart(), nil
	case "savecart", "10":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return SaveCart(), nil
	case "clearcart", "11":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return ClearCart(), nil
	
	case "exit", "quit", "12":
		fmt.Println("Exiting...")
		os.Exit(0)
	case "help", "13":
		print_menu()
		return "", nil
	default:
		return "", errors.New("Not a real command")
	}
	return "", errors.New("Not a real command")
}
