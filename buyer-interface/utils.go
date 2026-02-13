package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
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

func print_menu() {
	fmt.Print("Available commands:\n" +
		"1. \033[1mCreateAccount\033[0m - Sets up username and password, returns buyer ID\n" +
		"2. \033[1mLogin\033[0m - Login with username and password (starts session)\n" +
		"3. \033[1mLogout\033[0m - Ends active buyer session\n" +
		"4. \033[1mGetItem\033[0m - Returns Item details\n" +
		"5. \033[1mGetCategories\033[0m - Get a list of categories\n" +
		"6. \033[1mSearchItemsForSale\033[0m - Search items for sale by keywords\n" +
		"7. \033[1mAddItemToCart\033[0m - Add item to shopping cart\n" +
		"8. \033[1mRemoveItemFromCart\033[0m - Remove item from shopping cart\n" +
		"9. \033[1mDisplayCart\033[0m - Display items in shopping cart\n" +
		"10. \033[1mSaveCart\033[0m - Save the shopping cart\n" +
		"11. \033[1mClearCart\033[0m - Clear the shopping cart\n" +
		"12. \033[1mProvideFeedback\033[0m - Given an item ID, provide a thumbs up or thumbs down for the item\n" +
		"13. \033[1mGetSellerRating\033[0m - Given a seller ID, return the feedback for the seller\n" +
		"14. \033[1mGetBuyerPurchases\033[0m - Get a history of item IDs purchased by the buyer of the active session\n" +
		"15. \033[1mMakePurchase\033[0m - Purchase items in the remote cart\n" +
		"16. \033[1mExit\033[0m or \033[1mQuit\033[0m - Exit the application\n" +
		"17. \033[1mHelp\033[0m - Show this menu\n")
}

func dispatch_command(command string, reader *bufio.Reader) {
	command = strings.ToLower(command)

	switch command {
	case "createaccount", "register", "1":
		CreateAccount(reader)
	case "login", "2":
		Login(reader)
	case "logout", "3":
		Logout()
	case "getitem", "item", "4":
		GetItem(reader)
	case "getcategories", "categories", "5":
		GetCategories()
	case "searchitemsforsale", "search", "6":
		SearchItemsForSale(reader)
	case "additemtocart", "add", "7":
		AddItemToCart(reader)
	case "removeitemfromcart", "remove", "8":
		RemoveItemFromCart(reader)
	case "displaycart", "cart", "9":
		DisplayCart()
	case "savecart", "save", "10":
		SaveCart()
	case "clearcart", "clear", "11":
		ClearCart()
	case "providefeedback", "feedback", "12":
		ProvideFeedback(reader)
	case "getsellerrating", "rating", "13":
		GetSellerRating(reader)
	case "getbuyerpurchases", "purchases", "14":
		GetBuyerPurchases()
	case "makepurchase", "buy", "15":
		MakePurchase(reader)
	case "exit", "quit", "16":
		os.Exit(0)
	case "help", "17":
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

func sendDeleteRequest(endpoint string, payload interface{}) (string, error) {
	return sendRequest("DELETE", endpoint, payload)
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
