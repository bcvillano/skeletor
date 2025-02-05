#!/usr/bin/env python3

import argparse
import requests


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
        print("cmd = " + args.cmd)
    else:
        print("Unknown verb")

if __name__ == '__main__':
    main()