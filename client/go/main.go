package main

import (
	"fmt"
	//"net/http"
	"os/exec"
	"net"
	"time"
	"runtime"
)

var host string = "localhost"
var port int = 80

func runcmd(command string) ([]byte, error) {
	if runtime.GOOS == "windows" {
		return exec.Command("powershell", "/c", command).CombinedOutput()
	} else {
		return exec.Command("/bin/bash", "-c", command).CombinedOutput()
	}
}

func main() {
	server := "http://" + net.JoinHostPort(host, fmt.Sprintf("%d", port))
	counter := 0
	for true{
		fmt.Println("Counter: ", counter)
		fmt.Println("URL: ", server )
		output,err := runcmd("whoami; hostname")
		if err != nil {
			fmt.Println("Error: ", err)
		}else{
			fmt.Println("Output: ", string(output))
		}
		counter++
		time.Sleep(1 * time.Second)
	}
}