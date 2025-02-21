package model

// File represents a file stored in the system.
type File struct {
	ID   uint   `json:"id" gorm:"primaryKey;autoIncrement"`
	Name string `json:"name"`
	URL  string `json:"url"`
	Size int64  `json:"size"`
}
