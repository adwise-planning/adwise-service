package auth

import (
	"adwise-service/model"
	"adwise-service/repository"
	"adwise-service/utils"
	"errors"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

// AuthService handles user authentication and registration.
type AuthService struct {
	repo      repository.UserRepository
	jwtSecret string
}

// NewAuthService creates a new AuthService.
func NewAuthService(repo repository.UserRepository, jwtSecret string) *AuthService {
	return &AuthService{repo: repo, jwtSecret: jwtSecret}
}

// Register creates a new user with a hashed password.
func (s *AuthService) Register(user *model.User) error {
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(user.Password), bcrypt.DefaultCost)
	if err != nil {
		return err
	}
	user.Password = string(hashedPassword)
	return s.repo.CreateUser(user)
}

// Update user.
func (s *AuthService) UpdateUser(user *model.User) error {
	return s.repo.UpdateUser(user)
}

// Login authenticates a user and returns the user object.
func (s *AuthService) LoginUsingEmail(email, password string) (*model.User, error) {
	user, err := s.repo.FindUserByEmail(email)
	if err != nil {
		return nil, err
	}
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(password)); err != nil {
		return nil, errors.New("invalid credentials")
	}
	return user, nil
}

func (s *AuthService) LoginUsingPhone(country_code, phone, password string) (*model.User, error) {
	user, err := s.repo.FindUserByPhone(country_code, phone)
	if err != nil {
		return nil, err
	}
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(password)); err != nil {
		return nil, errors.New("invalid credentials")
	}
	return user, nil
}

// GetUserByID fetches a user by their ID.
func (s *AuthService) GetUserByID(userID uuid.UUID) (*model.User, error) {
	return s.repo.FindUserByID(userID)
}

// GetUserByEmail fetches a user by their Email.
func (s *AuthService) GetUserByEmail(email string) (*model.User, error) {
	return s.repo.FindUserByEmail(email)
}

// GetUserByPhone fetches a user by their Phone.
func (s *AuthService) GetUserByPhone(country_code, phone_number string) (*model.User, error) {
	return s.repo.FindUserByPhone(country_code, phone_number)
}

// GenerateTokens generates both access and refresh tokens.
func (s *AuthService) GenerateTokens(user *model.User) (string, string, error) {
	// Generate access token
	accessToken, err := s.generateToken(user.ID, user.Role, 15*time.Minute) // 15 minutes expiry
	if err != nil {
		return "", "", err
	}

	// Generate refresh token
	refreshToken, err := s.generateToken(user.ID, user.Role, 7*24*time.Hour) // 7 days expiry
	if err != nil {
		return "", "", err
	}

	return accessToken, refreshToken, nil
}

// generateToken generates a JWT token.
func (s *AuthService) generateToken(userID uuid.UUID, role string, expiry time.Duration) (string, error) {
	claims := jwt.MapClaims{
		"user_id": userID,
		"role":    role,
		"exp":     time.Now().Add(expiry).Unix(),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(s.jwtSecret))
}

// ValidateToken validates a JWT token.
func (s *AuthService) ValidateToken(tokenString string) (uuid.UUID, string, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, errors.New("invalid signing method")
		}
		return []byte(s.jwtSecret), nil
	})
	if err != nil {
		return uuid.Nil, "", err
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok || !token.Valid {
		return uuid.Nil, "", errors.New("invalid token claims")
	}

	userID, ok := claims["user_id"].(string)
	if !ok {
		return uuid.Nil, "", errors.New("invalid user ID in token")
	}

	role, ok := claims["role"].(string)
	if !ok {
		return uuid.Nil, "", errors.New("invalid role in token")
	}

	userUUID, err := utils.ConvertStringToUUID(userID)
	if err != nil {
		return uuid.Nil, "", err
	}

	return userUUID, role, nil
}

// GenerateResetToken generates a password reset token.
func (s *AuthService) GenerateResetToken(user *model.User) (string, error) {
	// Generate a token with a short expiry (e.g., 1 hour)
	token, err := s.generateToken(user.ID, user.Role, 1*time.Hour)
	if err != nil {
		return "", err
	}

	// Set the reset token and expiry in the user object
	user.ResetToken = token
	user.ResetTokenExpiry = time.Now().Add(1 * time.Hour)

	return token, nil
}

// ValidateResetToken validates a password reset token.
func (s *AuthService) ValidateResetToken(tokenString string) (uuid.UUID, error) {
	userID, _, err := s.ValidateToken(tokenString)
	if err != nil {
		return uuid.Nil, err
	}

	// Fetch the user from the database
	user, err := s.repo.FindUserByID(userID)
	if err != nil {
		return uuid.Nil, err
	}

	// Check if the token matches and is not expired
	if user.ResetToken != tokenString || time.Now().After(user.ResetTokenExpiry) {
		return uuid.Nil, errors.New("invalid or expired reset token")
	}

	return userID, nil
}
