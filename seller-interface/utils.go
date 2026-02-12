package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
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
func dispatch_command(command string, reader *bufio.Reader) {
	switch command {
	case "createaccount", "register", "1":
		CreateAccount(reader)
	case "login", "2":
		Login(reader)
	case "logout", "3":
		Logout(reader)
	case "getsellerrating", "rating", "4":
		GetSellerRating(reader)
	case "getcategories", "categories", "5":
		GetCategories()
	case "registeritemforsale", "sell", "6":
		RegisterItemForSale(reader)
	case "changeitemprice", "changeprice", "7":
		ChangeItemPrice(reader)
	case "updateunitsforsale", "updateqty", "8":
		UpdateUnitsForSale(reader)
	case "displayitemsforsale", "list", "9":
		DisplayItemsForSale()
	case "exit", "quit", "10":
		os.Exit(0)
	case "help", "11":
		print_menu()
	default:
		fmt.Printf("No such command: %s\n", command)
	}
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return fallback
}
func sendPostRequest(endpoint string, payload interface{}) (string, error) {
	return sendRequest("POST", endpoint, payload)
}

func sendPutRequest(endpoint string, payload interface{}) (string, error) {
	return sendRequest("PUT", endpoint, payload)
}

func sendRequest(method, endpoint string, payload interface{}) (string, error) {
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	req, err := http.NewRequest(method, serverURL+endpoint, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("connection error: %v", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(body), nil
}

func sendGetRequest(endpoint string, params url.Values) (string, error) {
	// Build the full URL with query parameters
	fullURL := fmt.Sprintf("%s%s?%s", serverURL, endpoint, params.Encode())

	resp, err := http.Get(fullURL)
	if err != nil {
		return "", fmt.Errorf("connection error: %v", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(body), nil
}
func DebugJSON(v interface{}) {
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		fmt.Println("DebugJSON error:", err)
		return
	}

	fmt.Println(string(data))
}

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}
