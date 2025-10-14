//go:build !windows

package main

import "os/exec"

func execCommand(command string) *exec.Cmd {
	return exec.Command("bash", "-c", command)
}