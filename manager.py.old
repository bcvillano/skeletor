#!/usr/bin/env python3

#Prototype of a interactive manager tool for skeletor.

import requests, re, json

URL = "http://127.0.0.1:80"

def skeletor_banner():
    try:
        with open("banner.txt", "r",encoding='utf-8') as f:
            banner = f.read()
            print(banner)
    except FileNotFoundError:
        pass


def menu():
    print("1. Get Agent Status")
    print("2. Issue a Command")
    print("3. Get Result from Agent")    
    print("4. Exit")

def exit_manager():
    print("Exiting...")
    exit(0)

def validate_ip(ip):
    ipv4_pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return re.match(ipv4_pattern, ip) is not None

def get_agent_status():
    try:
        agents = requests.get(URL + "/get-agents").json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return 
    if agents:
        for agent in agents:
            print(f"Agent ID: {agent['agent_id']}")
            print(f"Agent Status: {agent['status']}\n")

            
def send_cmd():
    requests.post(URL + "/clear-targets")
    command = input("Command: ")
    if command.strip() == "":
        print("Command cannot be empty.")
        return
    targets = input("Command Targets (comma separated) (Use * for all): ")
    if targets == "*":
        targets = []
        for agent in requests.get(URL + "/get-agents").json():
            targets.append(agent['agent_id'])
        requests.post(URL + "/set-targets", json={"ips": targets})
    else:
        targets = targets.strip().split(",")
        if "x" in targets:
            x_val = input("Number of teams: ")
            targets = targets.replace("x", x_val)
            print(f"Targets: {targets}")
            confirm = input("Confirm (y/n): ")
            if confirm.lower() != "y" and confirm.lower() != "yes":
                print("Command not sent.")
                return
            targets = targets.strip().split(",")
            for t in targets:
                if t.strip() != "":
                    data = {'agent_id': t, 'action': 'command', 'command': command}
                    requests.post("http://localhost:80/make-task", json=data)
        else:
            for t in targets:
                if t.strip() != "":
                    data = {'agent_id': t, 'action': 'command', 'command': command}
                    requests.post("http://localhost:80/make-task", json=data)

    for target in requests.get("http://localhost:80/targets").text.split("\n"):
            data = {'agent_id': target, 'action': 'command', 'command': command.strip()}
            requests.post("http://localhost:80/make-task", json=data)
    requests.post(URL + "/clear-targets")

def get_result():
    agent = input("Enter Agent ID to get last result from: ").strip()
    if validate_ip(agent):
        data = {"agent_id": agent}
        result = requests.post("http://localhost:80/get-result", json=data).json()
        result_str = "\n" + "Agent: " + agent + "\n" + "Command: " + result.get('command') + "\n" + "Result: " + result.get('result') + "\n"
        print(result_str)
    else:
        print("Invalid Agent ID. Please enter the IPv4 address of the agent\n")
        get_result()


def main():
    skeletor_banner()
    while True:
        menu()
        userin = input(": ").strip()
        options = {
            "1": get_agent_status,
            "2": send_cmd,
            "3": get_result,
            "4": exit_manager,
        }
        if userin in options:
            options[userin]()
        else:
            print("Invalid option. Please try again.")
        

if __name__ == "__main__":
    main()