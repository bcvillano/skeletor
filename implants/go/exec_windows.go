//go:build windows

package main

import (
	"os/exec"
	"syscall"
)

func execCommand(command string) *exec.Cmd {
	cmd := exec.Command("powershell", "-WindowStyle", "Hidden", "-Command", command)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	return cmd
}