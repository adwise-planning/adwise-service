package model

import "github.com/google/uuid"

type WebSocketMessage struct {
	Type       string      `json:"type"` // message, call, ice-candidate, ack
	ID         uint        `json:"id" gorm:"primaryKey;autoIncrement"`
	SenderID   uuid.UUID   `json:"sender_id"`
	ReceiverID uuid.UUID   `json:"receiver_id"`
	Content    string      `json:"content"`
	Status     string      `json:"status"`  // sent, delivered, read
	Payload    interface{} `json:"payload"` // Used for WebRTC offers, answers, and ICE candidates
}
