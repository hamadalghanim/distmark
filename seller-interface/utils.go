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
