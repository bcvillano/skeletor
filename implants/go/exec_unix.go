//go:build !windows

package main

import (
	"os/exec"
	"runtime"
)

func execCommand(command string) *exec.Cmd {
	if runtime.GOOS == "freebsd" {
		return exec.Command("sh", "-c", command)
	}
	return exec.Command("bash", "-c", command)
}
