package database

import (
	"adwise-service/model"

	"github.com/google/uuid"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type RelationalDB struct {
	db *gorm.DB
}

// NewRelationalDB creates a new relational database connection.
func NewRelationalDB(dsn string) (*RelationalDB, error) {
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	// db, err := gorm.Open(mongodb.Open(dsn), &gorm.Config{})
	if err != nil {
		return nil, err
	}

	// Auto-migrate models
	if err := db.AutoMigrate(&model.User{}, &model.Message{}, &model.File{}, &model.LoginUser{}, &model.UserPreference{}); err != nil {
		return nil, err
	}

	return &RelationalDB{db: db}, nil
}

func (r *RelationalDB) CreateUser(user *model.User) error {
	return r.db.Create(user).Error
}

// UpdateUser updates an existing user in the database.
func (r *RelationalDB) UpdateUser(user *model.User) error {
	// Update user using GORM's `Model` method with `Updates`, which will only update non-zero fields
	// If you don't want to overwrite the `Password` or `ResetToken`, they can be excluded
	return r.db.Model(&model.User{}).Where("id = ?", user.ID).Updates(model.User{
		CountryCode: user.CountryCode,
		PhoneNumber: user.PhoneNumber,
		Email:       user.Email,
		FirstName:   user.FirstName,
		MiddleName:  user.MiddleName,
		LastName:    user.LastName,
		DisplayName: user.DisplayName,
	}).Error
}

// FindUserByEmail finds a user by email.
func (r *RelationalDB) FindUserByEmail(email string) (*model.User, error) {
	var user model.User
	if err := r.db.Where("email = ?", email).First(&user).Error; err != nil {
		return nil, err
	}
	return &user, nil
}

// FindUserByPhone finds a user by phone.
func (r *RelationalDB) FindUserByPhone(country_code, phone_number string) (*model.User, error) {
	var user model.User
	if err := r.db.Where("country_code = ? and phone_number = ?", country_code, phone_number).First(&user).Error; err != nil {
		return nil, err
	}
	return &user, nil
}

// Validate User
func (r *RelationalDB) ValidateUser(user *model.User) (uuid.UUID, error) {
	var foundUser model.User
	err := r.db.Where("email = ? AND password = ?", user.Email, user.Password).First(&foundUser).Error
	if err != nil {
		return uuid.Nil, err
	}
	return foundUser.ID, nil
}

// FindUserByID finds a user by ID.
func (r *RelationalDB) FindUserByID(userID uuid.UUID) (*model.User, error) {
	var user model.User
	if err := r.db.First(&user, userID).Error; err != nil {
		return nil, err
	}
	return &user, nil
}

// CreateMessage saves a new message to the database.
func (r *RelationalDB) CreateMessage(message *model.Message) error {
	return r.db.Create(message).Error
}

// FindMessagesByUserID retrieves messages for a user.
func (r *RelationalDB) FindMessagesByUserID(userID uuid.UUID, limit int) ([]model.Message, error) {
	var messages []model.Message
	if err := r.db.Where("sender_id = ? OR receiver_id = ?", userID, userID).Limit(limit).Find(&messages).Error; err != nil {
		return nil, err
	}
	return messages, nil
}

// FindMessageByID retrieves a message by its ID.
func (r *RelationalDB) FindMessageByID(messageID uint) (*model.Message, error) {
	var message model.Message
	if err := r.db.First(&message, messageID).Error; err != nil {
		return nil, err
	}
	return &message, nil
}

// DeleteMessage deletes a message by its ID.
func (r *RelationalDB) DeleteMessage(messageID uint) error {
	return r.db.Delete(&model.Message{}, messageID).Error
}
