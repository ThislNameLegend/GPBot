package main

import (
    "log"
    "os"
    "time"

    "github.com/gofiber/fiber/v2"
    "github.com/gofiber/fiber/v2/middleware/cors"
    "github.com/golang-jwt/jwt/v5"
)

var jwtSecret = []byte(os.Getenv("JWT_SECRET"))
var users = map[string]string{
    "admin": "admin123",
    "user":  "user123",
}

type LoginRequest struct {
    Username string `json:"username"`
    Password string `json:"password"`
}

type User struct {
    ID       int    `json:"id"`
    Username string `json:"username"`
    Role     string `json:"role"`
}

func main() {
    app := fiber.New()
    app.Use(cors.New())

    // Health check
    app.Get("/health", func(c *fiber.Ctx) error {
        return c.JSON(fiber.Map{
            "status":  "ok",
            "service": "auth",
            "time":    time.Now().Unix(),
        })
    })

    // Login
    app.Post("/auth/login", func(c *fiber.Ctx) error {
        var req LoginRequest
        if err := c.BodyParser(&req); err != nil {
            return c.Status(400).JSON(fiber.Map{"error": "Invalid request"})
        }

        expectedPass, exists := users[req.Username]
        if !exists || expectedPass != req.Password {
            return c.Status(401).JSON(fiber.Map{"error": "Invalid credentials"})
        }

        // Create JWT token
        token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
            "username": req.Username,
            "role":     req.Username, // admin/user
            "exp":      time.Now().Add(24 * time.Hour).Unix(),
        })

        tokenString, err := token.SignedString(jwtSecret)
        if err != nil {
            return c.Status(500).JSON(fiber.Map{"error": "Cannot create token"})
        }

        return c.JSON(fiber.Map{
            "token":   tokenString,
            "user":    req.Username,
            "role":    req.Username,
            "expires": time.Now().Add(24 * time.Hour).Unix(),
        })
    })

    // Validate token
    app.Get("/auth/validate", func(c *fiber.Ctx) error {
        tokenString := c.Query("token")
        if tokenString == "" {
            return c.Status(400).JSON(fiber.Map{"error": "Token is required"})
        }

        token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
            return jwtSecret, nil
        })

        if err != nil || !token.Valid {
            return c.Status(401).JSON(fiber.Map{"valid": false, "error": "Invalid token"})
        }

        claims, ok := token.Claims.(jwt.MapClaims)
        if !ok {
            return c.Status(401).JSON(fiber.Map{"valid": false})
        }

        return c.JSON(fiber.Map{
            "valid": true,
            "user":  claims["username"],
            "role":  claims["role"],
            "exp":   claims["exp"],
        })
    })

    // Get user info
    app.Get("/auth/user", func(c *fiber.Ctx) error {
        tokenString := c.Get("Authorization")
        if len(tokenString) > 7 {
            tokenString = tokenString[7:] // Remove "Bearer "
        }

        token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
            return jwtSecret, nil
        })

        if err != nil || !token.Valid {
            return c.Status(401).JSON(fiber.Map{"error": "Unauthorized"})
        }

        claims, _ := token.Claims.(jwt.MapClaims)
        return c.JSON(fiber.Map{
            "id":       1001,
            "username": claims["username"],
            "role":     claims["role"],
            "email":    claims["username"].(string) + "@example.com",
        })
    })

    log.Println("✅ Auth service (Go) running on :8081")
    app.Listen(":8081")
}
