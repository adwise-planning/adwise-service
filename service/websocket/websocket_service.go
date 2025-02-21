package websocket

import (
	"adwise-service/model"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/json"
	"errors"
	"io"
	"log"
	"net/http"
	"sync"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all connections (customize for production)
	},
}

// WebSocketService manages WebSocket connections and messaging.
type WebSocketService struct {
	clients map[uuid.UUID]*websocket.Conn // Map user IDs to WebSocket connections
	mu      sync.Mutex
	key     []byte // Encryption key for end-to-end encryption
}

// NewWebSocketService creates a new WebSocketService.
func NewWebSocketService() *WebSocketService {
	// Generate a random encryption key (for demonstration purposes)
	key := make([]byte, 32)
	if _, err := rand.Read(key); err != nil {
		log.Fatalf("Failed to generate encryption key: %v", err)
	}

	return &WebSocketService{
		clients: make(map[uuid.UUID]*websocket.Conn),
		key:     key,
	}
}

// encrypt encrypts a message using AES-256.
func (s *WebSocketService) encrypt(plaintext []byte) ([]byte, error) {
	block, err := aes.NewCipher(s.key)
	if err != nil {
		return nil, err
	}

	ciphertext := make([]byte, aes.BlockSize+len(plaintext))
	iv := ciphertext[:aes.BlockSize]
	if _, err := io.ReadFull(rand.Reader, iv); err != nil {
		return nil, err
	}

	stream := cipher.NewCFBEncrypter(block, iv)
	stream.XORKeyStream(ciphertext[aes.BlockSize:], plaintext)

	return ciphertext, nil
}

// decrypt decrypts a message using AES-256.
func (s *WebSocketService) decrypt(ciphertext []byte) ([]byte, error) {
	block, err := aes.NewCipher(s.key)
	if err != nil {
		return nil, err
	}

	if len(ciphertext) < aes.BlockSize {
		return nil, errors.New("ciphertext too short")
	}

	iv := ciphertext[:aes.BlockSize]
	ciphertext = ciphertext[aes.BlockSize:]

	stream := cipher.NewCFBDecrypter(block, iv)
	stream.XORKeyStream(ciphertext, ciphertext)

	return ciphertext, nil
}

// HandleConnection handles a new WebSocket connection.
func (s *WebSocketService) HandleConnection(conn *websocket.Conn, userID uuid.UUID) {
	s.mu.Lock()
	s.clients[userID] = conn
	s.mu.Unlock()

	defer func() {
		s.mu.Lock()
		delete(s.clients, userID)
		s.mu.Unlock()
		conn.Close()
	}()

	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			log.Println("WebSocket read error:", err)
			break
		}

		// Decrypt the message
		// decryptedMessage, err := s.decrypt(message)
		// if err != nil {
		// 	log.Println("WebSocket decryption error:", err)
		// 	continue
		// }
		// log.Printf("Decrypted message: %s\n", decryptedMessage)

		log.Printf("Decrypted message: %s\n", message)

		// Unmarshal the message
		var msg model.Message
		if err := json.Unmarshal(message, &msg); err != nil {
			log.Println("WebSocket unmarshal error:", err)
			continue
		}

		// Handle different message types
		switch msg.Type {
		case "message":
			s.HandleMessage(userID, msg)
		case "call":
			s.handleCall(userID, msg)
		case "ice-candidate":
			s.handleICECandidate(userID, msg)
		// case "typing":
		// 	s.handleTyping(msg)
		// case "ack":
		// 	s.handleAcknowledgment(msg)
		default:
			log.Println("Unknown message type:", msg.Type)
		}

		// Broadcast the message to all clients
		// s.broadcast(msg)
	}
}

// handleMessage handles a one-to-one message.
func (s *WebSocketService) HandleMessage(senderID uuid.UUID, msg model.Message) {
	// Set the message status to "sent"
	msg.Status = "sent"

	// Send the message to the recipient
	recipientConn, ok := s.clients[msg.ReceiverID]
	if !ok {
		log.Println("Recipient not connected")
		return
	}

	// Marshal the message
	// messageBytes, err := json.Marshal(msg)
	// if err != nil {
	// 	log.Println("WebSocket marshal error:", err)
	// 	return
	// }
	// JSON Implementation
	if err := recipientConn.WriteJSON(msg); err != nil {
		log.Println("WebSocket write error:", err)
	}

	// Encrypt the message
	// encryptedMessage, err := s.encrypt(messageBytes)
	// if err != nil {
	// 	log.Println("WebSocket encryption error:", err)
	// 	return
	// }
	// if err := recipientConn.WriteMessage(websocket.TextMessage, encryptedMessage); err != nil {
	// 	log.Println("WebSocket write error:", err)
	// }

	// Send an acknowledgment back to the sender
	ack := model.WebSocketMessage{
		Type:       "ack",
		SenderID:   msg.ReceiverID,
		ReceiverID: msg.SenderID,
		ID:         msg.ID,
		Status:     "sent",
		Content:    "Message sent successfully",
	}
	senderConn, ok := s.clients[senderID]
	if !ok {
		log.Println("Sender not connected")
		return
	}

	if err := senderConn.WriteJSON(ack); err != nil {
		log.Println("WebSocket write error:", err)
	}
}

// handleCall handles a WebRTC call setup.
func (s *WebSocketService) handleCall(senderID uuid.UUID, msg model.Message) {
	// Forward the call offer to the recipient
	recipientConn, ok := s.clients[msg.ReceiverID]
	if !ok {
		log.Println("Recipient not connected")
		return
	}

	if err := recipientConn.WriteJSON(msg); err != nil {
		log.Println("WebSocket write error:", err)
	}
}

// handleICECandidate handles WebRTC ICE candidates.
func (s *WebSocketService) handleICECandidate(senderID uuid.UUID, msg model.Message) {
	// Forward the ICE candidate to the recipient
	recipientConn, ok := s.clients[msg.ReceiverID]
	if !ok {
		log.Println("Recipient not connected")
		return
	}

	if err := recipientConn.WriteJSON(msg); err != nil {
		log.Println("WebSocket write error:", err)
	}
}

// // handleTyping handles a typing indicator.
// func (s *WebSocketService) handleTyping(msg model.Message) {
// 	// Broadcast the typing indicator to the recipient
// 	s.broadcast(msg)
// }

// // handleAcknowledgment handles a message acknowledgment.
// func (s *WebSocketService) handleAcknowledgment(msg model.Message) {
// 	// Update the message status to "delivered" or "read"
// 	s.broadcast(msg)
// }

// // broadcast sends a message to all connected clients.
// func (s *WebSocketService) broadcast(msg model.Message) {
// 	s.mu.Lock()
// 	defer s.mu.Unlock()

// 	// Marshal the message
// 	messageBytes, err := json.Marshal(msg)
// 	if err != nil {
// 		log.Println("WebSocket marshal error:", err)
// 		return
// 	}

// 	// Encrypt the message
// 	encryptedMessage, err := s.encrypt(messageBytes)
// 	if err != nil {
// 		log.Println("WebSocket encryption error:", err)
// 		return
// 	}

// 	// Send the message to all clients
// 	for client := range s.clients {
// 		if err := client.WriteMessage(websocket.TextMessage, encryptedMessage); err != nil {
// 			log.Println("WebSocket write error:", err)
// 			client.Close()
// 			delete(s.clients, client)
// 		}
// 	}

// 	// May be duplicate
// 	for client := range s.clients {
// 		if err := client.WriteJSON(msg); err != nil {
// 			log.Println("WebSocket write error:", err)
// 			client.Close()
// 			delete(s.clients, client)
// 		}
// 	}
// }
