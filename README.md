# Skeletor

Skeletor is a HTTP C2 (command and control) client/server application built upon the Flask framework designed for red vs. blue cyber security competitions.  
Skeletor clients communicate on a beaconing system, sending outbound POST requests to the Skeletor server's **/tasks** route every 120 seconds containing JSON data in the format:
```json
{
  "agent_id": "192.168.1.9"
}
```  
where agent_id is typically the local ip address of the agent, which is important for allowing us to see the local ip for identifying boxes in many red vs blue competitions. Optionally, agent_id could have 
a different identifier, depending on how you wish to identify different agents. 

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
Currently, the skelctl command line utility is the primary way of interacting with the skeletor server.  
