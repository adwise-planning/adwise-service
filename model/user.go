package model

import (
	"time"

	"github.com/google/uuid"
)

// User represents a user in the system.
type User struct {
	ID          uuid.UUID `gorm:"primaryKey;default:gen_random_uuid()" json:"id"`
	CountryCode string    `gorm:"not null" json:"country_code"`
	PhoneNumber string    `gorm:"unique;not null" json:"phone_number"`
	Email       string    `gorm:"unique;not null" json:"email"`
	FirstName   string    `gorm:"not null" json:"first_name"`
	MiddleName  string    `gorm:"" json:"middle_name,omitempty"`
	LastName    string    `gorm:"not null" json:"last_name"`
	DisplayName string    `gorm:"default:'Anonymous'" json:"display_name"` // Field ignored by GORM, but included in JSON serialization with a custom name
	Password    string    `gorm:"not null" json:"password"`
	Role        string    `gorm:"default:user" json:"role"` // Default role is "user"
	CreatedAt   time.Time `json:"created_at,omitempty"`
	UpdatedAt   time.Time `json:"updated_at,omitempty"`

	// Security and Authentication
	PasswordHash        string    `gorm:"not null" json:"password_hash,omitempty"`          // Hashed password (instead of plain text password)
	PasswordSalt        string    `gorm:"" json:"password_salt,omitempty"`                  // Salt for password hashing (if needed)
	IsEmailVerified     bool      `gorm:"default:false" json:"is_email_verified"`           // Whether the user's email has been verified
	IsPhoneVerified     bool      `gorm:"default:false" json:"is_phone_verified"`           // Whether the user's phone number has been verified
	EmailVerifiedAt     time.Time `json:"email_verified_at,omitempty"`                      // Time when email was verified
	PhoneVerifiedAt     time.Time `json:"phone_verified_at,omitempty"`                      // Time when phone number was verified
	FailedLoginAttempts int       `gorm:"default:0" json:"failed_login_attempts,omitempty"` // Number of failed login attempts
	AccountLockedUntil  time.Time `json:"account_locked_until,omitempty"`                   // Account lock expiration time, if the account is locked
	RefreshToken        string    `gorm:"" json:"refresh_token,omitempty"`                  // Not stored in DB, used only for token refresh
	ResetToken          string    `gorm:"" json:"reset_token,omitempty"`                    // Password reset token
	ResetTokenExpiry    time.Time `gorm:"" json:"reset_token_expiry,omitempty"`             // Password reset token expiry

	// Social Media Integration (Optional)
	GoogleID   string `json:"google_id,omitempty"`   // Google social login ID (if applicable)
	FacebookID string `json:"facebook_id,omitempty"` // Facebook social login ID (if applicable)
	TwitterID  string `json:"twitter_id,omitempty"`  // Twitter social login ID (if applicable)

	// Timestamps
	LastLoginAt time.Time `json:"last_login_at,omitempty"` // Timestamp for the last login
	LastLoginIP string    `json:"last_login_ip,omitempty"` // IP address from the last login

}
