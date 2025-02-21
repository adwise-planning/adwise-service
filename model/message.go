package model

import (
	"time"

	"github.com/google/uuid"
)

// Message represents a real-time message.
type Message struct {
	ID         uint      `json:"id" gorm:"primaryKey;autoIncrement"`
	SenderID   uuid.UUID `json:"sender_id"`
	ReceiverID uuid.UUID `json:"receiver_id"`
	Content    string    `json:"content"`
	Type       string    `gorm:"default:'text'" json:"type,omitempty"` // e.g., "text", "audio", "video", "call", "ice-candidate", "ack"
	Timestamp  time.Time `json:"timestamp"`                            // Timestamp when the message was sent
	Status     string    `json:"status"`                               // sent, delivered, read, failed
	CreatedAt  time.Time `json:"created_at"`
	// Payload           interface{}            `json:"payload,omitempty"`      // Used for WebRTC offers, answers, and ICE candidates
	IsEncrypted      bool      `json:"is_encrypted,omitempty"` // Whether the message content is encrypted (for security)
	EncryptionStatus string    `json:"encryption_status,omitempty"`
	MediaThumbnail   string    `json:"media_thumbnail,omitempty"` // URL to the thumbnail of media (if available)
	MediaURL         string    `json:"media_url,omitempty"`
	MediaType        string    `json:"media_type,omitempty"`
	MediaSize        int64     `json:"media_size,omitempty"`
	MediaDuration    uint      `json:"media_duration,omitempty"`
	ReplyToID        uuid.UUID `json:"reply_to_id,omitempty"`
	// ReadBy            []uint                 `json:"read_by,omitempty"`
	IsStarred       bool    `json:"is_starred,omitempty"`
	IsReadReceipt   bool    `json:"is_read_receipt,omitempty"`   // Whether the receiver has seen the message (for tracking read status)
	IsSystemMessage bool    `json:"is_system_message,omitempty"` // True if the message is a system message (e.g., notifications, alerts)
	LocationLat     float64 `json:"location_lat,omitempty"`
	LocationLng     float64 `json:"location_lng,omitempty"`
	// Tags              []string               `json:"tags,omitempty"`
	// Reactions         []string               `json:"reactions,omitempty"`
	IsEdited        bool      `json:"is_edited,omitempty"`
	EditedAt        time.Time `json:"edited_at,omitempty"`
	ForwardedFromID uint      `json:"forwarded_from_id,omitempty"`
	IsForwarded     bool      `json:"is_forwarded,omitempty"`
	DeliveredAt     time.Time `json:"delivered_at,omitempty"`
	ExpiresAt       time.Time `json:"expires_at,omitempty"`
	AutoDelete      bool      `json:"auto_delete,omitempty"`
	Priority        string    `json:"priority,omitempty"`
	GroupID         uint      `json:"group_id,omitempty"`
	// TranslatedContent map[string]string      `json:"translated_content,omitempty"`
	// CustomAttributes  map[string]interface{} `json:"custom_attributes,omitempty"`
	GlobalMessageID string `json:"global_message_id,omitempty"`
	IsPinned        bool   `json:"is_pinned,omitempty"`
	ForwardCount    uint   `json:"forward_count,omitempty"`
	DisplayStatus   string `json:"display_status,omitempty"`
	// CustomTags        []string               `json:"custom_tags,omitempty"`
	Transcription string `json:"transcription,omitempty"`
	ErrorMessage  string `json:"error_message,omitempty"`
	// Mentions          []uint                 `json:"mentions,omitempty"`
	Language        string    `json:"language,omitempty"`         // Language of the message (e.g., "en", "fr", etc.)
	DeliveryAttempt uint      `json:"delivery_attempt,omitempty"` // Number of delivery attempts (in case of failed message delivery)
	ExpiryTimestamp time.Time `json:"expiry_timestamp,omitempty"` // Expiry time for the message (for messages with expiration like self-destruct)

}
