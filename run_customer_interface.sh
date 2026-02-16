#!/bin/bash

echo "Buyer Frontend Client"
echo "1. Local (http://localhost:8001)"
echo "2. GCP (http://34.72.178.240:80)"
echo "3. Custom"
read -p "Select environment (1, 2, or 3): " choice

case $choice in
    1)
        SERVER_URL="http://localhost:8001"
        ;;
    2)
        SERVER_URL="http://34.72.178.240:80"
        ;;
    3)
        read -p "Enter custom server URL: " SERVER_URL
        ;;
    *)
        echo "Invalid choice, defaulting to local"
        SERVER_URL="http://localhost:8001"
        ;;
esac

echo "Connecting to: $SERVER_URL"
cd buyer-interface
go run *.go -server "$SERVER_URL"