package handlers

import (
	"adwise-service/service/auth"
	"adwise-service/service/file"
	"adwise-service/service/message"
	"adwise-service/service/websocket"
	"net/http"
)

// Server represents the API server.
type Server struct {
	authService      auth.AuthService
	messageService   message.MessageService
	fileService      file.FileService
	websocketService websocket.WebSocketService
	httpServer       *http.Server
	middleware       []func(http.Handler) http.Handler
}

// NewServer creates a new API server.
func NewServer(
	authService auth.AuthService,
	messageService message.MessageService,
	fileService file.FileService,
	websocketService websocket.WebSocketService,
	httpServer *http.Server,
	middleware []func(http.Handler) http.Handler,
) *Server {
	return &Server{
		authService:      authService,
		messageService:   messageService,
		fileService:      fileService,
		websocketService: websocketService,
		httpServer:       httpServer,
		middleware:       middleware,
	}
}
