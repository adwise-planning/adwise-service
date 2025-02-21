package configuration

import (
	"errors"
	"os"
)

// Config holds all configuration settings for the application.
type Config struct {
	ServerPort    string // Port on which the server will run
	DatabaseURL   string // Connection string for the relational database
	Neo4jURI      string // Neo4j connection URI
	Neo4jUsername string // Neo4j username
	Neo4jPassword string // Neo4j password
	S3Bucket      string // AWS S3 bucket name for file storage
	S3Region      string // AWS S3 region
	JWTSecret     string // Secret key for JWT signing
}

// LoadConfig loads configuration from environment variables.
func LoadConfig() (*Config, error) {
	cfg := &Config{
		ServerPort: getEnv("SERVER_PORT", "8080"),
		// DatabaseURL:   getEnv("DATABASE_URL", "postgresql://admin:rsg80kYOY6qbbbBfSwWwdcjxF6gYevFP@dpg-cu796edds78s73aq6iu0-a.oregon-postgres.render.com/adwise?options=-c%20search_path=data"),
		DatabaseURL:   getEnv("DATABASE_URL", "postgresql://admin:npg_Lxe83skfqKTg@ep-steep-sound-a5jr9vda-pooler.us-east-2.aws.neon.tech/adwise?search_path=data&sslmode=require"),
		Neo4jURI:      getEnv("NEO4J_URI", "localhost"),
		Neo4jUsername: getEnv("NEO4J_USERNAME", ""),
		Neo4jPassword: getEnv("NEO4J_PASSWORD", ""),
		S3Bucket:      getEnv("S3_BUCKET", ""),
		S3Region:      getEnv("S3_REGION", ""),
		JWTSecret:     getEnv("JWT_SECRET", "secret_key"),
	}

	// Validate required configurations
	if cfg.DatabaseURL == "" {
		return nil, errors.New("DATABASE_URL is required")
	}
	if cfg.Neo4jURI == "" {
		return nil, errors.New("NEO4J_URI is required")
	}
	if cfg.JWTSecret == "" {
		return nil, errors.New("JWT_SECRET is required")
	}

	return cfg, nil
}

// getEnv retrieves environment variables with a fallback default value.
func getEnv(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}
