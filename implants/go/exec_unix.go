//go:build !windows

package main

import (
	"os/exec"
	"runtime"
)

func execCommand(command string) (string, error) {
	if runtime.GOOS == "freebsd" {
		out, err := exec.Command("sh", "-c", command).Output()
		if err != nil {
			return "", err
		}
		return string(out), nil
	}
	out, err := exec.Command("bash", "-c", command).Output()
	if err != nil {
		return "", err
	}
	return string(out), nil
}
