package middleware

import (
	"adwise-service/service/auth"
	"adwise-service/utils"
	"context"
	"errors"
	"net/http"
	"strings"

	"github.com/golang-jwt/jwt/v5"
	"go.uber.org/zap"
)

// Define custom types for context keys
type contextKey string

const (
	// Declare constants for the context keys
	KeyUser contextKey = "user"
	KeyRole contextKey = "role"
)

// AuthMiddleware is a middleware for JWT-based authentication.
type AuthMiddleware struct {
	authService auth.AuthService
	jwtSecret   string
}

// NewAuthMiddleware creates a new AuthMiddleware.
func NewAuthMiddleware(authService auth.AuthService, jwtSecret string) *AuthMiddleware {
	return &AuthMiddleware{
		authService: authService,
		jwtSecret:   jwtSecret,
	}
}

// Middleware validates the JWT token and sets the user in the request context.
func (m *AuthMiddleware) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {

		// Skip authentication for the registration endpoint
		if r.URL.Path == "/api/register" || r.URL.Path == "/api/login" ||
			r.URL.Path == "/api/admin" || r.URL.Path == "/api/request-reset" ||
			r.URL.Path == "/api/reset-password" {
			next.ServeHTTP(w, r)
			return
		}
		// Extract the token from the Authorization header
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			utils.LogWarn("Authorization header is missing")
			http.Error(w, "Authorization header is required", http.StatusUnauthorized)
			return
		}

		// Check if the header is in the format "Bearer <token>"
		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || parts[0] != "Bearer" {
			utils.LogWarn("Invalid authorization header format")
			http.Error(w, "Invalid authorization header format", http.StatusUnauthorized)
			return
		}

		tokenString := parts[1]

		// Parse and validate the token
		token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, errors.New("invalid signing method")
			}
			return []byte(m.jwtSecret), nil
		})
		if err != nil {
			utils.LogWarn("Invalid token", zap.Error(err))
			http.Error(w, "Invalid token", http.StatusUnauthorized)
			return
		}

		// Extract claims
		claims, ok := token.Claims.(jwt.MapClaims)
		if !ok || !token.Valid {
			utils.LogWarn("Invalid token claims")
			http.Error(w, "Invalid token claims", http.StatusUnauthorized)
			return
		}

		// Get the user ID from the claims
		userID, ok := claims["user_id"].(string)
		if !ok {
			utils.LogWarn("Invalid user ID in token")
			http.Error(w, "Invalid user ID in token", http.StatusUnauthorized)
			return
		}

		utils.LogInfo("Userid: " + userID)

		// Parse and validate the token
		userUUID, role, err := m.authService.ValidateToken(tokenString)
		if err != nil {
			utils.LogWarn("Invalid token", zap.Error(err))
			http.Error(w, "Invalid token", http.StatusUnauthorized)
			return
		}

		// Fetch the user from the database
		user, err := m.authService.GetUserByID(userUUID)
		if err != nil {
			utils.LogWarn("User not found", zap.Error(err))
			http.Error(w, "User not found", http.StatusUnauthorized)
			return
		}

		// Add the user to the request context
		ctx := context.WithValue(r.Context(), KeyUser, user)
		ctx = context.WithValue(ctx, KeyRole, role)
		utils.LogInfo("User authenticated", zap.Any("user_id", user.ID), zap.String("role", role))
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}
