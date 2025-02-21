package message

import (
	"adwise-service/model"
	"adwise-service/repository"
	"time"

	"github.com/google/uuid"
)

// MessageService handles message storage and retrieval.
type MessageService struct {
	repo repository.MessageRepository
}

// NewMessageService creates a new MessageService.
func NewMessageService(repo repository.MessageRepository) *MessageService {
	return &MessageService{repo: repo}
}

// SaveMessage saves a new message to the database.
func (s *MessageService) SaveMessage(message *model.Message) error {
	message.CreatedAt = time.Now()
	return s.repo.CreateMessage(message)
}

// GetMessages retrieves messages for a user.
func (s *MessageService) GetMessages(userID uuid.UUID, limit int) ([]model.Message, error) {
	return s.repo.FindMessagesByUserID(userID, limit)
}

// GetMessageByID retrieves a message by its ID.
func (s *MessageService) GetMessageByID(messageID uint) (*model.Message, error) {
	return s.repo.FindMessageByID(messageID)
}

// DeleteMessage deletes a message by its ID.
func (s *MessageService) DeleteMessage(messageID uint) error {
	return s.repo.DeleteMessage(messageID)
}
