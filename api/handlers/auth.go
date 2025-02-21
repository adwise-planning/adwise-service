package handlers

import (
	"adwise-service/model"
	"adwise-service/utils"
	"encoding/json"
	"net/http"

	"go.uber.org/zap"
	"golang.org/x/crypto/bcrypt"
)

// handleRegister handles user registration.
func (s *Server) HandleRegister(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var user model.User
	if err := json.NewDecoder(r.Body).Decode(&user); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if user.Email == "" || user.Password == "" {
		http.Error(w, "Email and password are required", http.StatusBadRequest)
		return
	}

	if err := s.authService.Register(&user); err != nil {
		http.Error(w, "Failed to register user", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"message": "User registered successfully"})
}

// handleLogin handles user login.
func (s *Server) HandleLogin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var login_user model.LoginUser
	var user *model.User
	if err := json.NewDecoder(r.Body).Decode(&login_user); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	var err error
	if login_user.IsEmailLogin {
		user, err = s.authService.LoginUsingEmail(login_user.Email, login_user.Password)
	} else {
		user, err = s.authService.LoginUsingPhone(login_user.CountryCode, login_user.PhoneNumber, login_user.Password)
	}

	if err != nil {
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}

	// Generate JWT token (to be implemented)
	refresh_token, token, _ := s.authService.GenerateTokens(user)

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"uuid": string(user.ID.String()), "token": token, "refresh_token": refresh_token})
}

// handleRefresh handles token refresh requests.
func (s *Server) HandleRefresh(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var request struct {
		RefreshToken string `json:"refresh_token"`
	}
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	// Validate the refresh token
	userID, _, err := s.authService.ValidateToken(request.RefreshToken)
	if err != nil {
		http.Error(w, "Invalid refresh token", http.StatusUnauthorized)
		return
	}

	// Fetch the user from the database
	user, err := s.authService.GetUserByID(userID)
	if err != nil {
		http.Error(w, "User not found", http.StatusUnauthorized)
		return
	}

	// Generate new tokens
	accessToken, refreshToken, err := s.authService.GenerateTokens(user)
	if err != nil {
		http.Error(w, "Failed to generate tokens", http.StatusInternalServerError)
		return
	}

	// Return the new tokens
	response := map[string]string{
		"access_token":  accessToken,
		"refresh_token": refreshToken,
	}
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// handleAdminEndpoint handles an admin-only endpoint.
func (s *Server) HandleAdminEndpoint(w http.ResponseWriter, r *http.Request) {
	// Get the role from the request context
	role := r.Context().Value("role").(string)

	// Check if the user is an admin
	if role != "admin" {
		utils.LogWarn("Unauthorized access attempt", zap.String("role", role))
		http.Error(w, "Unauthorized", http.StatusForbidden)
		return
	}

	// Proceed with the admin-only logic
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Welcome, admin!"})
}

// handleRequestReset handles password reset requests.
func (s *Server) HandleRequestReset(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var request struct {
		Email string `json:"email"`
	}
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	// Fetch the user by email
	user, err := s.authService.GetUserByEmail(request.Email)
	if err != nil {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	// Generate a password reset token
	resetToken, err := s.authService.GenerateResetToken(user)
	if err != nil {
		http.Error(w, "Failed to generate reset token", http.StatusInternalServerError)
		return
	}

	// Send the reset token via email (to be implemented)
	utils.LogInfo("Password reset token generated", zap.String("email", user.Email), zap.String("reset_token", resetToken))

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Password reset token sent to your email"})
}

// handleResetPassword handles password reset.
func (s *Server) HandleResetPassword(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var request struct {
		Token    string `json:"token"`
		Password string `json:"password"`
	}
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	// Validate the reset token
	userID, err := s.authService.ValidateResetToken(request.Token)
	if err != nil {
		http.Error(w, "Invalid or expired reset token", http.StatusUnauthorized)
		return
	}

	// Fetch the user from the database
	user, err := s.authService.GetUserByID(userID)
	if err != nil {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	// Hash the new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(request.Password), bcrypt.DefaultCost)
	if err != nil {
		http.Error(w, "Failed to hash password", http.StatusInternalServerError)
		return
	}

	// Update the user's password
	user.Password = string(hashedPassword)

	if err := s.authService.Register(user); err != nil {
		http.Error(w, "Failed to update password", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Password reset successfully"})
}
