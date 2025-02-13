package main

import (
	"fmt"
	//"net/http"
	//"os/exec"
	"net"
	"time"
)

var host string = "localhost"
var port int = 80

func main() {
	server := "http://" + net.JoinHostPort(host, fmt.Sprintf("%d", port))
	counter := 0
	for true{
		fmt.Println("Counter: ", counter)
		fmt.Println("URL: ", server )
		counter++
		time.Sleep(1 * time.Second)
	}
}