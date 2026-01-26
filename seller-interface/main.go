package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"regexp"
	"strconv"
	"strings"
)

const serverAddress = "localhost:8000"

var SessionId int = 0

func main() {

	conn, err := connectWithRetry(serverAddress)
	if err != nil {
		fmt.Println("Error connecting:", err.Error())
		os.Exit(1)
	}
	defer conn.Close() // Ensure the connection is closed when main function exits.

	fmt.Println("Connected to server at " + conn.RemoteAddr().String())
	print_menu()
	for {
		reader := bufio.NewReader(os.Stdin)
		fmt.Print("\nEnter command: ")
		command, err := reader.ReadString('\n')
		if err != nil {
			fmt.Println("Error reading input:", err)
			continue
		}
		command = strings.ToLower(strings.TrimSpace(command))

		message, err := dispatch_command(command)
		if err != nil {
			fmt.Println("Error handling command:", err)
			continue
		}
		_, err = conn.Write([]byte(message))
		if err != nil {
			fmt.Println("Connection lost:", err)
			fmt.Println("Attempting to reconnect...")

			conn.Close()
			newConn, err := connectWithRetry(serverAddress)
			if err != nil {
				fmt.Println("Reconnection failed:", err)
				return
			}
			conn = newConn
			fmt.Println("Reconnected successfully!")
			continue // Retry the command
		}

		buffer := make([]byte, 1024)
		n, err := conn.Read(buffer)
		if err != nil {
			if err == io.EOF {
				fmt.Println("Server closed connection")
			} else {
				fmt.Println("Error reading from server:", err)
			}

			fmt.Println("Attempting to reconnect...")
			conn.Close()
			newConn, err := connectWithRetry(serverAddress)
			if err != nil {
				fmt.Println("Reconnection failed:", err)
				return
			}
			conn = newConn
			fmt.Println("Reconnected successfully!")
			continue
		}

		handle_post_command(buffer, n)
		fmt.Print(string(buffer[:n]))
	}
}

func handle_post_command(buffer []byte, n int) {
	if strings.HasPrefix(strings.TrimSpace(string(buffer[:n])), "Login successful. Session ID:") {
		// the buffer will have the session Id
		re := regexp.MustCompile("[0-9]+")
		match := re.Find(buffer[:n])
		if match != nil {
			id, err := strconv.Atoi(string(match))
			if err == nil {
				SessionId = id
				return
			} else {
				fmt.Println("Failed to parse session id:", err)
			}
		} else {
			fmt.Println("No session id found in server response")
		}
	}
	if strings.TrimSpace(string(buffer[:n])) == "logout successful" {
		SessionId = 0
	}
	if strings.TrimSpace(string(buffer[:n])) == "Session no longer valid" {
		SessionId = 0
	}
}
