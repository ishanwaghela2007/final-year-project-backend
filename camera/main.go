package main

import (
	"camera/db"
	"camera/middleware"
	"camera/routes"
	"camera/utils"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis_rate/v10"
	"github.com/joho/godotenv"
)

func main() {
	//-----------env setup------------------
	if err := godotenv.Load(); err != nil {
		log.Fatal("Error loading .env file")
	}
	log.Println("env loaded successfully")
    //----------redis setup----------------
	utils.ConnectRedis()
    //----------cassandra setup------------
	db.ConnectCassandra()
    //----------router setup---------------
	router := gin.Default()
	router.Use(middleware.NewRedisUserRateLimiter(utils.RDB, redis_rate.PerMinute(10)))
	router.GET("/ping", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "pong",
			"status":  http.StatusOK,
		})
	})
	router.Group("api/v0/cctv")
	router.Use(middleware.CameraAccess())
	router.GET("/stream/channel1",
		routes.CameraChannel1,
	)
	router.GET("/stream/channel2",
		routes.CameraChannel2,
	)
	router.GET("/stream/channel3",
		routes.CameraChannel3,
	)
	router.GET("/stream/channel4",
		routes.CameraChannel4,
	)
	router.Run(":3000") // listens on 0.0.0.0:8080 by default
}