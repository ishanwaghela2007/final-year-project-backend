package main

import (
	"Auth/db"
	"Auth/middleware"
	"Auth/routes"
	"fmt"
	"log"
	"net/http"
	"os"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("⚠️  .env file not found — using system defaults")
	}


	// Get environment variables
	port := getEnv("PORT", "8080")
	httpProxy := os.Getenv("HTTP_PROXY")
	httpsProxy := os.Getenv("HTTPS_PROXY")

	// Set proxy environment variables if provided
	setProxyEnv(httpProxy, httpsProxy)

	

	// Initialize Cassandra
	db.ConnectCassandra()
	defer db.Close()

	// Run DB setup tasks
	db.CreateUserTable()
	db.BootstrapAdmin()

	// Initialize Gin router
	router := gin.Default()

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "ok",
			"message": "Server is configured properly",
		})
	})

	// API routes
	api := router.Group("/api/v1")
	{
		api.POST("/login", routes.Login)
	}

	// Admin routes (protected)
	admin := router.Group("/api/v1/admin")
	admin.Use(middleware.AuthMiddleware("admin"))
	{
		admin.POST("/users", routes.CreateUser)
		admin.DELETE("/users/:email", routes.DeleteUser)
	}

	// Start server
	fmt.Printf("🌐 HTTP Proxy: %s\n", httpProxy)
	fmt.Printf("🔒 HTTPS Proxy: %s\n", httpsProxy)
	fmt.Printf("🚀 Server running on port %s\n", port)

	if err := router.Run(":" + port); err != nil {
		log.Fatalf("❌ Failed to start server: %v", err)
	}
}

// getEnv returns the environment variable or a default value
func getEnv(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}

// setProxyEnv sets HTTP/HTTPS proxy environment variables if provided
func setProxyEnv(httpProxy, httpsProxy string) {
	if httpProxy != "" {
		os.Setenv("HTTP_PROXY", httpProxy)
	}
	if httpsProxy != "" {
		os.Setenv("HTTPS_PROXY", httpsProxy)
	}
}
