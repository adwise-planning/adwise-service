package repository

import (
	"adwise-service/model"

	"github.com/google/uuid"
)

// UserRepository defines the interface for user-related database operations.
type UserRepository interface {
	CreateUser(user *model.User) error
	UpdateUser(user *model.User) error
	FindUserByEmail(email string) (*model.User, error)
	FindUserByPhone(country_code, phone_number string) (*model.User, error)
	FindUserByID(userID uuid.UUID) (*model.User, error)
}

// MessageRepository defines the interface for message-related database operations.
type MessageRepository interface {
	CreateMessage(message *model.Message) error
	FindMessagesByUserID(userID uuid.UUID, limit int) ([]model.Message, error)
	FindMessageByID(messageID uint) (*model.Message, error)
	DeleteMessage(messageID uint) error
}
