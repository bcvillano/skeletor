//go:build windows

package main

import (
	"os/exec"
	"syscall"
)

func execCommand(command string) (string, error) {
	cmd := exec.Command("powershell", "-WindowStyle", "Hidden", "-Command", command)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	out, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return string(out), nil
}
