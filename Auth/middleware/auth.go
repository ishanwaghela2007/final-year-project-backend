package middleware


import (
	"net/http"
	"strings"

	"Auth/utils"
	"github.com/gin-gonic/gin"
)

func AuthMiddleware(requiredRole string) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Missing token"})
			c.Abort()
			return
		}

		token := strings.TrimPrefix(authHeader, "Bearer ")
		claims, err := utils.ParseToken(token)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid or expired token"})
			c.Abort()
			return
		}

		role, ok := claims["role"].(string)
		if !ok {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token claims"})
			c.Abort()
			return
		}

		if requiredRole == "admin" && role != "admin" {
			c.JSON(http.StatusForbidden, gin.H{"error": "Access denied: admin only"})
			c.Abort()
			return
		}

		c.Set("user_id", claims["user_id"])
		c.Set("role", role)
		c.Next()
	}
}
