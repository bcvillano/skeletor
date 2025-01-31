#!/usr/bin/env python3

import argparse


def arg_setup():
    msg = "Command line tool for interaction with Skeletor C2 server running on localhost"
    parser = argparse.ArgumentParser(description = msg)
    parser.add_argument("verb",help="skelctl verb defining action to take",choices=['get','cmd'])
    return parser.parse_args()

def main():
    args = arg_setup()
    if args.verb == 'get':
        pass
    elif args.verb == 'cmd':
        pass
    else:
        print("Unknown verb")

if __name__ == '__main__':
    main()