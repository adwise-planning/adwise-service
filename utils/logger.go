package utils

import (
	"os"

	"github.com/fatih/color" // For colored output
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

var Logger *zap.Logger

// InitializeLogger initializes the Zap logger with string-based output.
func InitializeLogger() {
	// Configure the logger's encoder with time in ISO8601 format.
	config := zap.NewProductionEncoderConfig()
	config.EncodeTime = zapcore.ISO8601TimeEncoder
	// Use a console encoder for both production and development to avoid JSON.
	var encoder zapcore.Encoder

	// Use console encoder in both environments for string output
	if os.Getenv("ENV") == "development" {
		consoleConfig := zap.NewDevelopmentEncoderConfig()
		consoleConfig.EncodeTime = zapcore.ISO8601TimeEncoder
		encoder = zapcore.NewConsoleEncoder(consoleConfig)
	} else {
		// Use console encoder in production as well for string format
		consoleConfig := zap.NewProductionEncoderConfig()
		consoleConfig.EncodeTime = zapcore.ISO8601TimeEncoder
		encoder = zapcore.NewConsoleEncoder(consoleConfig)
	}

	// Create a core that writes logs to Stdout at Info level
	core := zapcore.NewCore(encoder, zapcore.AddSync(os.Stdout), zapcore.InfoLevel)

	// Create the logger instance with caller information
	Logger = zap.New(core, zap.AddCaller(), zap.AddStacktrace(zapcore.ErrorLevel))

	// Ensure logs are flushed before the application exits
	defer Logger.Sync()
}

// LogError logs an error message with additional fields and includes the caller information.
func LogError(message string, err error, fields ...zap.Field) {
	// Enhance the output with some colored styling for error level
	if os.Getenv("ENV") == "development" {
		color.Red("ERROR: %s: %v", message, err)
	} else {
		// Logs with caller information (file & line number)
		Logger.Error(message, append(fields, zap.Error(err))...)
	}
}

// LogInfo logs an info message with additional fields and includes the caller information.
func LogInfo(message string, fields ...zap.Field) {
	// Enhancing info logs with a distinct color in development
	if os.Getenv("ENV") == "development" {
		color.Cyan("INFO: %s", message)
	} else {
		// Logs with caller information (file & line number)
		Logger.Info(message, fields...)
	}
}

// LogDebug logs a debug message with additional fields and includes the caller information.
func LogDebug(message string, fields ...zap.Field) {
	// Adding a distinct color for debug level in development mode
	if os.Getenv("ENV") == "development" {
		color.HiWhite("DEBUG: %s", message)
	} else {
		// Logs with caller information (file & line number)
		Logger.Debug(message, fields...)
	}
}

// LogWarn logs a warning message with additional fields and includes the caller information.
func LogWarn(message string, fields ...zap.Field) {
	// Enhancing the output of warning logs
	if os.Getenv("ENV") == "development" {
		color.Yellow("WARN: %s", message)
	} else {
		// Logs with caller information (file & line number)
		Logger.Warn(message, fields...)
	}
}
