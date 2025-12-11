package routes

import (
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/gocql/gocql"
	"golang.org/x/crypto/bcrypt"

	"Auth/db"
	"Auth/utils"
)

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
	IsLoggedIn bool `json:"isloggedin"`
}

func Login(c *gin.Context) {
	var req LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var id gocql.UUID
	var role, hashedPassword string

	query := `SELECT id, password, role FROM users WHERE email = ? LIMIT 1`
	if err := db.Session.Query(query, req.Email).Consistency(gocql.One).Scan(&id, &hashedPassword, &role); err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
		return
	}

	// ✅ Compare bcrypt hash properly
	if err := bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(req.Password)); err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
		return
	}

	// Update isloggedin in DB
	if err := db.Session.Query(`UPDATE users SET isloggedin = ? WHERE email = ?`, true, req.Email).Exec(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update login status"})
		return
	}

	req.IsLoggedIn = true
	token, err := utils.GenerateToken(id.String(), role, req.Email)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":    "Login successful",
		"token":      token,
		"role":       role,
		"isloggedin": req.IsLoggedIn,
	})
}

func Logout(c *gin.Context) {
	email := c.GetString("email")
	if email == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized request"})
		return
	}

	// Update isloggedin to false
	if err := db.Session.Query(`UPDATE users SET isloggedin = ? WHERE email = ?`, false, email).Exec(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to logout"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Logout successful",
		"token":   "", // Return empty token
	})
}
func Oauthlogin(c *gin.Context) {
	fmt.Println("Oauth login")
}