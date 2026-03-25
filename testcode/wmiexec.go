package main

import (
	"fmt"
	"os/exec"
)

func wmiExec(command string) {
	wmicommand := "powershell -Command \"" + command + " > /Users/Public/log.txt\""
	fmt.Print(wmicommand + "\n")
	// We use the WMI class Win32_Process and call its 'Create' method.
	// This tells the Windows Management Instrumentation service to start the process.
	wmiCommand := fmt.Sprintf("(Get-WmiObject -List | Where-Object {$_.Name -eq 'Win32_Process'}).Create('%s')", wmicommand)

	cmd := exec.Command("powershell", "-Command", wmiCommand)

	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("Error: %s\n", err)
		return
	}

	fmt.Printf("WMI Execution Result: %s\n", string(output))
}

func main() {
	wmiExec("whoami")
}
