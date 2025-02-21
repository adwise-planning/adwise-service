package file

import (
	"adwise-service/model"
	"log"
	"mime/multipart"
	"path/filepath"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
	"github.com/google/uuid"
)

// FileService handles file uploads and downloads.
type FileService struct {
	s3Bucket string
	s3Region string
	uploader *s3manager.Uploader
}

// NewFileService creates a new FileService.
func NewFileService(s3Bucket, s3Region string) *FileService {
	// Initialize AWS session
	sess, err := session.NewSession(&aws.Config{
		Region: aws.String(s3Region),
	})
	if err != nil {
		log.Fatalf("Failed to create AWS session: %v", err)
	}

	return &FileService{
		s3Bucket: s3Bucket,
		s3Region: s3Region,
		uploader: s3manager.NewUploader(sess),
	}
}

// UploadFile uploads a file to S3 and returns the file URL.
func (s *FileService) UploadFile(file multipart.File, header *multipart.FileHeader) (*model.File, error) {
	// Generate a unique file name
	fileName := generateUniqueFileName(header.Filename)

	// Upload the file to S3
	_, err := s.uploader.Upload(&s3manager.UploadInput{
		Bucket: aws.String(s.s3Bucket),
		Key:    aws.String(fileName),
		Body:   file,
	})
	if err != nil {
		return nil, err
	}

	// Generate the file URL
	fileURL := "https://" + s.s3Bucket + ".s3." + s.s3Region + ".amazonaws.com/" + fileName

	return &model.File{
		Name: header.Filename,
		URL:  fileURL,
		Size: header.Size,
	}, nil
}

// DownloadFile downloads a file from S3.
func (s *FileService) DownloadFile(fileName string) ([]byte, error) {
	// Initialize AWS session
	sess, err := session.NewSession(&aws.Config{
		Region: aws.String(s.s3Region),
	})
	if err != nil {
		return nil, err
	}

	// Download the file from S3
	downloader := s3manager.NewDownloader(sess)
	buf := aws.NewWriteAtBuffer([]byte{})

	_, err = downloader.Download(buf, &s3.GetObjectInput{
		Bucket: aws.String(s.s3Bucket),
		Key:    aws.String(fileName),
	})
	if err != nil {
		return nil, err
	}

	return buf.Bytes(), nil
}

// generateUniqueFileName generates a unique file name.
func generateUniqueFileName(originalName string) string {
	ext := filepath.Ext(originalName)
	return uuid.New().String() + ext
}
