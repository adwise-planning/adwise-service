package websocket

import (
	"encoding/json"

	"github.com/gorilla/websocket"
)

// SendJSON sends a JSON message over a WebSocket connection.
func SendJSON(conn *websocket.Conn, v interface{}) error {
	message, err := json.Marshal(v)
	if err != nil {
		return err
	}
	return conn.WriteMessage(websocket.TextMessage, message)
}

// ReadJSON reads a JSON message from a WebSocket connection.
func ReadJSON(conn *websocket.Conn, v interface{}) error {
	_, message, err := conn.ReadMessage()
	if err != nil {
		return err
	}
	return json.Unmarshal(message, v)
}
