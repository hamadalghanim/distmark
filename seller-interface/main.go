package main

import (
	"bufio"
	"fmt"
	"net"
	"os"
)

func main() {
	// Connect to the TCP server running on localhost at port 8080.
	// Ensure the server is running before executing this client code.
	conn, err := net.Dial("tcp", "localhost:8000")
	if err != nil {
		fmt.Println("Error connecting:", err.Error())
		os.Exit(1)
	}
	defer conn.Close() // Ensure the connection is closed when main function exits.

	fmt.Println("Connected to server at " + conn.RemoteAddr().String())
	for {
		reader := bufio.NewReader(os.Stdin)
		fmt.Print("\nEnter command: ")
		message, _ := reader.ReadString('\n')

		_, err = conn.Write([]byte(message))
		if err != nil {
			fmt.Println("Error writing to server:", err.Error())
			return
		}

		// Buffer to read response from the server.
		buffer := make([]byte, 1024)
		n, err := conn.Read(buffer)
		if err != nil {
			fmt.Println("Error reading from server:", err.Error())
			return
		}

		fmt.Printf(string(buffer[:n]))
	}
}
