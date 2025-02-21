package handlers

import (
	"adwise-service/model"
	"adwise-service/utils"
	"encoding/json"
	"log"
	"net/http"
	"strings"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
	"go.uber.org/zap"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all connections (customize for production)
	},
}

// Test
func (s *Server) HandleWebSocket_OLD(w http.ResponseWriter, r *http.Request) {
	token := r.Header.Get("Authorization")
	userUUID, token, role := s.ValidateToken(token)
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		utils.LogError("Failed to upgrade connection: %v\n", err)
		http.Error(w, "Failed to upgrade to WebSocket", http.StatusInternalServerError)
		return
	}
	defer conn.Close()

	AddConnection(userUUID, token, conn)
	defer RemoveConnection(userUUID, token)

	log.Printf("User: %s connected as %s.\n", userUUID, role)

	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			log.Printf("Read error for user %s: %v\n", "userID", err)
			break
		}
		var msg model.Message
		if err := json.Unmarshal(message, &msg); err != nil {
			log.Println("WebSocket unmarshal error:", err)
			continue
		}
		s.websocketService.HandleMessage(userUUID, msg)
	}
}

// handleWebSocket handles WebSocket connections.
func (s *Server) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	// userID := r.Context().Value("user_id")
	token := r.Header.Get("Authorization")
	userUUID, _, _ := s.ValidateToken(token)
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		http.Error(w, "Failed to upgrade to WebSocket", http.StatusInternalServerError)
		return
	}
	defer conn.Close()
	s.websocketService.HandleConnection(conn, userUUID)
}

// Validate Token
func (s *Server) ValidateToken(bearerToken string) (uuid.UUID, string, string) {
	// Check if the header is in the format "Bearer <token>"
	parts := strings.Split(bearerToken, " ")
	if len(parts) != 2 || parts[0] != "Bearer" {
		utils.LogWarn("Invalid authorization header format")
		return uuid.Nil, bearerToken, "unathorized"
	}

	tokenString := parts[1]

	// Parse and validate the token
	userUUID, role, err := s.authService.ValidateToken(tokenString)
	if err != nil {
		utils.LogWarn("Invalid token", zap.Error(err))
		return uuid.Nil, tokenString, "unathorized"
	}
	return userUUID, tokenString, role
}
