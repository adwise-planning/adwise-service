package handlers

import (
	"encoding/json"
	"net/http"
)

// handleFiles handles file uploads and downloads.
func (s *Server) HandleFiles(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodPost:
		s.uploadFile(w, r)
	case http.MethodGet:
		s.downloadFile(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// uploadFile handles file uploads.
func (s *Server) uploadFile(w http.ResponseWriter, r *http.Request) {
	file, header, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "Failed to read file", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Upload the file
	uploadedFile, err := s.fileService.UploadFile(file, header)
	if err != nil {
		http.Error(w, "Failed to upload file", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(uploadedFile)
}

// downloadFile handles file downloads.
func (s *Server) downloadFile(w http.ResponseWriter, r *http.Request) {
	fileID := r.URL.Query().Get("id")
	if fileID == "" {
		http.Error(w, "File ID is required", http.StatusBadRequest)
		return
	}

	// Download the file
	fileBytes, err := s.fileService.DownloadFile(fileID)
	if err != nil {
		http.Error(w, "Failed to download file", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", "application/octet-stream")
	w.Write(fileBytes)
}
