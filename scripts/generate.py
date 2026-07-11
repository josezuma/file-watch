#!/usr/bin/env python3
import sys, json, argparse
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = {"name": "file-watch", "ready": True}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result}")
if __name__ == "__main__":
    main()
