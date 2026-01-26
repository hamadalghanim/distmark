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
		"4. \033[1mGetSellerRating\033[0m - Returns feedback for current seller\n" +
		"5. \033[1mGetCategories\033[0m - Get a list of categories\n" +
		"6. \033[1mRegisterItemForSale\033[0m - Register item with attributes and quantity, returns item ID\n" +
		"7. \033[1mChangeItemPrice\033[0m - Update item price by item ID\n" +
		"8. \033[1mUpdateUnitsForSale\033[0m - Remove quantity from item ID\n" +
		"9. \033[1mDisplayItemsForSale\033[0m - Display items on sale by current seller\n" +
		"10. \033[1mExit\033[0m or \033[1mQuit\033[0m - Exit the application\n" +
		"11. \033[1mHelp\033[0m - Show this menu\n")
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
	case "getsellerrating", "4":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return GetSellerRating(), nil
	case "getcategories", "5":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return GetCategories(), nil
	case "registeritemforsale", "6":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return RegisterItemForSale(reader), nil
	case "changeitemprice", "7":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return ChangeItemPrice(reader), nil
	case "updateunitsforsale", "8":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return UpdateUnitsForSale(reader), nil
	case "displayitemsforsale", "9":
		if SessionId == 0 {
			fmt.Println("Need to login first")
			return "", errors.New("Not logged in")
		}
		return DisplayItemsForSale(), nil
	case "exit", "quit", "10":
		fmt.Println("Exiting...")
		os.Exit(0)
	case "help", "11":
		print_menu()
		return "", nil
	default:
		return "", errors.New("Not a real command")
	}
	return "", errors.New("Not a real command")
}
