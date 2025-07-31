package main

import (
	"fmt"
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

func main(){
	fmt.Println("Hello, World!")
	fmt.Println("I'll finish this client later.")
}