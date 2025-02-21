package model

import (
	"time"

	"github.com/google/uuid"
)

type UserPreference struct {
	ID                 uint      `json:"id" gorm:"primaryKey;autoIncrement"`
	UserID             uuid.UUID `gorm:"unique;not null" json:"user_id"`          // Foreign key to the User model
	LanguagePreference string    `gorm:"default:'en'" json:"language_preference"` // Language preference (e.g., 'en', 'fr', etc.)
	ThemePreference    string    `gorm:"default:'light'" json:"theme_preference"` // Theme preference (e.g., 'light', 'dark')
	NotificationPref   bool      `gorm:"default:true" json:"notification_pref"`   // Whether the user wants to receive notifications
	Is2FAEnabled       bool      `gorm:"default:false" json:"is_2fa_enabled"`     // Whether 2FA is enabled for the user
	TwoFAMethod        string    `gorm:"" json:"two_fa_method,omitempty"`         // The method of 2FA (e.g., "TOTP", "SMS")
	IsDarkMode         bool      `gorm:"default:false" json:"is_dark_mode"`       // Dark mode preference

	// Miscellaneous Preferences
	// CustomPreferences map[string]interface{} `gorm:"" json:"custom_preferences,omitempty"` // A JSON field to store any other custom preferences (e.g., app-specific)

	// Timestamps
	UpdatedAt time.Time `json:"updated_at"`
}
