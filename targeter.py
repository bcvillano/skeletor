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

def ansible_ini():
    pass

def ansible_yaml():
    pass

def main():
    print("Skeletor Targeter\n")
    print("1. Template String (Ex: 10.10.x.1)")
    print("2. All targets")
    print("3. Ansible Inventory Groups")
    print("4. Exit")

    mode = input("Mode: ").strip()
    match mode:
        case "1":
            template_str = input("Template String (format 10.x.10.1): ").strip()
            num_teams = int(input("Number of teams: ").strip())
            print(template(template_str,num_teams))
        case "2":
            print(all_targets())
        case "3":
            print("Ansible Inventory File Format:")
            print("1. .ini\n2. .yaml\n3. Cancel")
            userin = input(": ")
            if userin.upper().strip() in ["1",".INI","INI"]:
                ansible_ini()
            elif userin.upper().strip() in ["2",".YAML","YAML"]:
                ansible_yaml()
            elif userin.upper().strip() == "3":
                main()
            else:
                print("Invalid Option")
                return
        case "4":
            return
        case _:
            print("Invalid mode")
            return

if __name__ == "__main__":
    main()