package main

import (
	"Feedback/routes"
	"fmt"
	"log"
	"net/http"
	"os"

	"Feedback/db"

	"github.com/joho/godotenv"
)

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Println("Warning: .env file not found, using system environment variables")
	}
	// 1. Get Port
	port := os.Getenv("PORT")
	if port == "" {
		port = "8081"
	}

	// 2. Connect DB
	db.ConnectCassandra()
	defer db.Close()
	db.CreateMessageTable()

	// 3. Start Both Hubs in Background
	go routes.C_Hub.Run() // Chat Hub
	go routes.N_Hub.Run() // Notification Hub

	// 4. Define Routes
	// -> Staff/Admin connect here to chat
	http.HandleFunc("/ws/chat", routes.ChatHandler)
	
	// -> Users connect here to receive alerts
	http.HandleFunc("/ws/notifications", routes.NotificationHandler)

	// -> Internal Microservices hit this to trigger alerts
	http.HandleFunc("/internal/notify", routes.TriggerNotificationHandler)

	// 5. Start Server
	fmt.Printf("Feedback Service started on :%s\n", port)
	fmt.Printf(" - Chat: ws://localhost:%s/ws/chat\n", port)
	fmt.Printf(" - Notif: ws://localhost:%s/ws/notifications\n", port)
	
	log.Fatal(http.ListenAndServe(":"+port, nil))
}