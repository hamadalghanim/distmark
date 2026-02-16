package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strings"
)

var serverURL string
var SessionId int = 0

func main() {
	// Define command-line flag
	flag.StringVar(&serverURL, "server", getEnv("SERVER_ADDRESS", "http://localhost:8001"), "Server URL")
	flag.Parse()

	fmt.Println("Buyer Frontend Client (HTTP)")
	fmt.Printf("Connected to: %s\n", serverURL)

	print_menu()
	scanner := bufio.NewReader(os.Stdin)

	for {
		fmt.Print("\nEnter command: ")

		command, err := scanner.ReadString('\n')
		if err != nil {
			fmt.Println("Input error:", err)
			return
		}

		command = strings.TrimSpace(command)
		if command == "" {
			continue
		}

		dispatch_command(command, scanner)
	}
}
