package api

import (
	"adwise-service/api/handlers"
	"adwise-service/service/auth"
	"adwise-service/service/file"
	"adwise-service/service/message"
	"adwise-service/service/websocket"
	"adwise-service/utils"
	"context"
	"log"
	"net/http"
	"time"

	"go.uber.org/zap"
)

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

// UseMiddleware adds middleware to the server.
func (s *Server) UseMiddleware(middleware func(http.Handler) http.Handler) {
	s.middleware = append(s.middleware, middleware)
}

// Start starts the HTTP server.
func (s *Server) Start(port string) error {
	// Initialize router
	router := s.initRouter()

	// Apply middleware
	var handler http.Handler = router
	for _, mw := range s.middleware {
		handler = mw(handler)
	}

	// Wrap the handler with logging middleware
	handler = s.loggingMiddleware(handler)

	// Create HTTP server
	s.httpServer = &http.Server{
		Addr:    ":" + port,
		Handler: handler,
	}

	// Start server in a goroutine
	go func() {
		utils.LogInfo("Server is running", zap.String("port", port))
		if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			utils.LogError("Failed to start server", err)
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Graceful shutdown
	quit := make(chan struct{})
	<-quit

	utils.LogInfo("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := s.httpServer.Shutdown(ctx); err != nil {
		utils.LogError("Server shutdown error", err)
		return err
	}

	utils.LogInfo("Server stopped gracefully")
	return nil
}

// initRouter initializes the HTTP router and registers routes.
func (s *Server) initRouter() *http.ServeMux {
	router := http.NewServeMux()
	h := handlers.NewServer(s.authService, s.messageService, s.fileService, s.websocketService, s.httpServer, s.middleware)
	// Register routes
	router.HandleFunc("/api/register", h.HandleRegister)
	router.HandleFunc("/api/login", h.HandleLogin)
	router.HandleFunc("/api/admin", h.HandleAdminEndpoint)          // Admin-only endpoint
	router.HandleFunc("/api/request-reset", h.HandleRequestReset)   // Request password reset
	router.HandleFunc("/api/reset-password", h.HandleResetPassword) // Reset password
	router.HandleFunc("/api/refresh", h.HandleRefresh)
	router.HandleFunc("/api/messages", h.HandleMessages)
	router.HandleFunc("/api/files", h.HandleFiles)
	router.HandleFunc("/ws", h.HandleWebSocket)

	return router
}

// loggingMiddleware logs incoming requests.
func (s *Server) loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		utils.LogInfo("Incoming request",
			zap.String("method", r.Method),
			zap.String("path", r.URL.Path),
			zap.String("remote_addr", r.RemoteAddr),
		)

		// Call the next handler
		next.ServeHTTP(w, r)

		// Log the response details
		utils.LogInfo("Request completed",
			zap.String("method", r.Method),
			zap.String("path", r.URL.Path),
			zap.String("remote_addr", r.RemoteAddr),
			zap.Duration("duration", time.Since(start)),
		)
	})
}
