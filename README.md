# Skeletor

Skeletor is a HTTP C2 (command and control) built upon the Flask framework designed for red vs. blue cyber security competitions.  
Skeletor clients communicate on a beaconing system, sending outbound POST requests to the Skeletor server containing JSON data in the format:
```json
{
  "agent_id": "192.168.1.9"
}
```  
where agent_id is typically the local ip address of the agent, which is important for allowing us to see the local ip for identifying boxes in many red vs blue competitions. Optionally, agent_id could have 
a different identifier, depending on how you wish to identify different agents. 
