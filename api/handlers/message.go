package handlers

import (
	"adwise-service/model"
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/google/uuid"
)

// handleMessages handles sending and retrieving messages.
func (s *Server) HandleMessages(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.getMessages(w, r)
	case http.MethodPost:
		s.sendMessage(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// sendMessage sends a new message
func (s *Server) sendMessage(w http.ResponseWriter, r *http.Request) {
	var message model.Message
	if err := json.NewDecoder(r.Body).Decode(&message); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	if err := s.messageService.SaveMessage(&message); err != nil {
		http.Error(w, "Failed to send message", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"message": "Message sent successfully"})
}

func (s *Server) getMessages(w http.ResponseWriter, r *http.Request) {
	userID := r.URL.Query().Get("user_id")
	if userID == "" {
		http.Error(w, "User ID is required", http.StatusBadRequest)
		return
	}

	limitStr := r.URL.Query().Get("limit")
	limit := 10 // Default limit
	if limitStr != "" {
		var err error
		limit, err = strconv.Atoi(limitStr)
		if err != nil {
			http.Error(w, "Invalid limit", http.StatusBadRequest)
			return
		}
	}

	// Parse the string into a uuid.UUID
	uuidValue, err := uuid.Parse(userID)
	if err != nil {
		return
	}
	// userIDUint, err := strconv.ParseUint(userID, 10, 64)
	// if err != nil {
	// 	http.Error(w, "Invalid user ID", http.StatusBadRequest)
	// 	return
	// }

	messages, err := s.messageService.GetMessages(uuidValue, limit)
	if err != nil {
		http.Error(w, "Failed to retrieve messages", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(messages)
}
