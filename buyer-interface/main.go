package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

var serverURL = getEnv("SERVER_ADDRESS", "http://localhost:8001")

var SessionId int = 0

func main() {
	fmt.Println("Buyer Frontend Client (HTTP)")

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
