package utils

import (
	"github.com/google/uuid"
)

// GenerateUUID generates a new UUID.
func GenerateUUID() string {
	return uuid.New().String()
}

func ConvertStringToUUID(value string) (uuid.UUID, error) {
	// Parse the string into a uuid.UUID
	uuidValue, err := uuid.Parse(value)
	if err != nil {
		return uuid.Nil, err // Return the Nil UUID if parsing fails
	}
	return uuidValue, nil
}
