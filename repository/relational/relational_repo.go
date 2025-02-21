package relational

import (
	"adwise-service/database"
	"adwise-service/model"

	"github.com/google/uuid"
)

// RelationalRepo implements the UserRepository interface for relational databases.
type RelationalRepo struct {
	db *database.RelationalDB
}

// NewRelationalRepo creates a new RelationalRepo.
func NewRelationalRepo(db *database.RelationalDB) *RelationalRepo {
	return &RelationalRepo{db: db}
}

// CreateUser creates a new user in the database.
func (r *RelationalRepo) CreateUser(user *model.User) error {
	return r.db.CreateUser(user)
}

// UpdateUser updates an existing user in the database.
func (r *RelationalRepo) UpdateUser(user *model.User) error {
	return r.db.UpdateUser(user)
}

// FindUserByEmail finds a user by email.
func (r *RelationalRepo) FindUserByEmail(email string) (*model.User, error) {
	return r.db.FindUserByEmail(email)
}

// FindUserByPhone finds a user by phone.
func (r *RelationalRepo) FindUserByPhone(country_code, phone_number string) (*model.User, error) {
	return r.db.FindUserByPhone(country_code, phone_number)
}

// FindUserByID finds a user by ID.
func (r *RelationalRepo) FindUserByID(userID uuid.UUID) (*model.User, error) {
	return r.db.FindUserByID(userID)
}

// CreateMessage saves a new message to the database.
func (r *RelationalRepo) CreateMessage(message *model.Message) error {
	return r.db.CreateMessage(message)
}

// FindMessagesByUserID retrieves messages for a user.
func (r *RelationalRepo) FindMessagesByUserID(userID uuid.UUID, limit int) ([]model.Message, error) {
	// var messages []model.Message
	messages, err := r.db.FindMessagesByUserID(userID, limit)
	if err != nil {
		return nil, err
	}
	return messages, nil
}

// FindMessageByID retrieves a message by its ID.
func (r *RelationalRepo) FindMessageByID(messageID uint) (*model.Message, error) {
	// var message model.Message
	message, err := r.db.FindMessageByID(messageID)
	if err != nil {
		return nil, err
	}
	return message, nil
}

// DeleteMessage deletes a message by its ID.
func (r *RelationalRepo) DeleteMessage(messageID uint) error {
	return r.db.DeleteMessage(messageID)
}
