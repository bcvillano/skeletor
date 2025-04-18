#!/usr/bin/env python3

import requests

def all_targets(): #returns all targets in the skeletor database (only works on same box as skeletor server) 
    target_str = ""
    agents = requests.get("http://localhost:80/get-agents").json()
    for agent in agents: 
        target_str += agent.get('agent_id') + ","
    target_str = target_str[:-1] #remove last comma
    return target_str

def template(template_str,num_teams): #formats a template string into a list of targets  
    target_str = ""
    for i in range(1,num_teams+1):
        targ = template_str.replace("x", str(i))
        target_str += targ + ","
    target_str = target_str[:-1] #remove last comma
    return target_str

def main():
    print("Skeletor Targeter\n")
    print("1. All targets")
    print("2. Template String (Ex: 10.10.x.1)")
    print("3. Exit")

    mode = input("Mode: ").strip()
    match mode:
        case "1":
            print(all_targets())
        case "2":
            template_str = input("Template String (format 10.x.10.1): ").strip()
            num_teams = int(input("Number of teams: ").strip())
            print(template(template_str,num_teams))
        case "3":
            return
        case _:
            print("Invalid mode")
            return

if __name__ == "__main__":
    main()