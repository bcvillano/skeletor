package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os/exec"
	"runtime"
	"time"
)

type Heartbeat struct {
	IP string `json:"ip"`
}

var (
	server = "localhost"
	port int = 80
	localIP,_ = GetLocalIP()
)

func GetLocalIP() (string, error) {
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		return "", err
	}

	for _, addr := range addrs {
		if ipNet, ok := addr.(*net.IPNet); ok && !ipNet.IP.IsLoopback() {
			if ipNet.IP.To4() != nil {
				return ipNet.IP.String(), nil
			}
		}
	}
	return "", fmt.Errorf("no local IP found")
}

func runcmd(command string) ([]byte, error) {
	if runtime.GOOS == "windows" {
		return exec.Command("powershell", "/c", command).CombinedOutput()
	} else {
		return exec.Command("/bin/bash", "-c", command).CombinedOutput()
	}
}

func heartbeat() {
	server := "http://" + net.JoinHostPort(server, fmt.Sprintf("%d", port)) + "/heartbeat"
	heartbeat := Heartbeat{IP: localIP}
	jsonData, err := json.Marshal(heartbeat)
	if err != nil {
		panic(err)
	}
	for {
		request, err := http.NewRequest("POST", server, bytes.NewBuffer(jsonData))
		if err != nil {
			fmt.Println(err)
		}
		request.Header.Set("Content-Type", "application/json; charset=UTF-8")
		client := &http.Client{}
		response, err := client.Do(request)
		if err != nil {
			panic(err)
		}
		defer response.Body.Close()
		time.Sleep(120 * time.Second)
	}
}

func main() {
	heartbeat()
	server := "http://" + net.JoinHostPort(server, fmt.Sprintf("%d", port))
	counter := 0
	for true {
		fmt.Println("Counter: ", counter)
		fmt.Println("URL: ", server)
		fmt.Println("Local IP: ", localIP)
		output, err := runcmd("whoami; hostname")
		if err != nil {
			fmt.Println("Error: ", err)
		} else {
			fmt.Println("Output: ", string(output))
		}
		counter++
		time.Sleep(1 * time.Second)
	}
}
