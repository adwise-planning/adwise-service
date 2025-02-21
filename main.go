package main

import (
	"adwise-service/api"
	"adwise-service/api/middleware"
	config "adwise-service/configuration"
	"adwise-service/database"
	"adwise-service/repository/relational"
	"adwise-service/service/auth"
	"adwise-service/service/file"
	"adwise-service/service/message"
	"adwise-service/service/websocket"
	"adwise-service/utils"
	"log"
	"net/http"

	"github.com/rs/cors"

	"go.uber.org/zap"
)

func main() {
	// Initialize logger
	utils.InitializeLogger()
	utils.LogInfo("Logger initialized")

	// Load configuration
	cfg, err := config.LoadConfig()
	if err != nil {
		utils.LogError("Failed to load config", err)
		log.Fatalf("Failed to load config: %v", err)
	}

	// Initialize relational database connection
	relationalDB, err := database.NewRelationalDB(cfg.DatabaseURL)
	if err != nil {
		utils.LogError("Failed to connect to relational database", err)
		log.Fatalf("Failed to connect to relational database: %v", err)
	}

	// // Initialize Neo4j database connection
	// neo4jDB, err := database.NewNeo4jDB(cfg.Neo4jURI, cfg.Neo4jUsername, cfg.Neo4jPassword)
	// if err != nil {
	// 	utils.LogError("Failed to connect to Neo4j database", err)
	// 	log.Fatalf("Failed to connect to Neo4j database: %v", err)
	// }
	// defer neo4jDB.Close()

	// Initialize repositories
	relationalRepo := relational.NewRelationalRepo(relationalDB)
	// graphRepo := graph.NewGraphRepo(neo4jDB)

	// print(graphRepo)
	// Initialize services
	authService := *auth.NewAuthService(relationalRepo, cfg.JWTSecret)
	messageService := *message.NewMessageService(relationalRepo)
	fileService := *file.NewFileService(cfg.S3Bucket, cfg.S3Region)
	websocketService := *websocket.NewWebSocketService()

	// Initialize authentication middleware
	authMiddleware := middleware.NewAuthMiddleware(authService, cfg.JWTSecret)

	// Initialize http server
	httpServer := &http.Server{
		Addr: ":" + cfg.ServerPort,
	}

	corsHandler := cors.New(cors.Options{
		AllowedOrigins:   []string{"*"}, // Allow only your frontend
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Content-Type", "Authorization"},
		AllowCredentials: true, // if cookies or credentials are being used
	})

	// Start API server
	server := api.NewServer(authService, messageService, fileService, websocketService, httpServer, nil)
	server.UseMiddleware(authMiddleware.Middleware)
	// Use the CORS middleware
	server.UseMiddleware(corsHandler.Handler)
	utils.LogInfo("Starting server", zap.String("port", cfg.ServerPort))
	if err := server.Start(cfg.ServerPort); err != nil {
		utils.LogError("Failed to start server", err)
		log.Fatalf("Failed to start server: %v", err)
	}
}
