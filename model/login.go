package model

import "time"

type LoginUser struct {
	CountryCode  string    `gorm:"unique;not null" json:"country_code"`
	PhoneNumber  string    `gorm:"unique;not null" json:"phone_number"`
	Email        string    `gorm:"unique;not null" json:"email"`
	Password     string    `gorm:"not null" json:"password"`
	IsEmailLogin bool      `gorm:"default:false" json:"is_email_login"`
	Role         string    `gorm:"default:'user'" json:"role"` // Default role is "user"
	LoginAt      time.Time `json:"login_at"`
}
