#!/usr/bin/env python3
"""
Reads jsonl from stdin and (re)-assigns numbers.

This doesn't use the dataset loader so there's no last-wins logic
applied to the input.
"""
import sys
import json


def main():
    print("(reading from stdin)", file=sys.stderr)
    n = 0
    for line in sys.stdin.readlines():
        obj = json.loads(line)
        obj["n"] = n
        n += 1
        print(json.dumps(obj))


if __name__ == "__main__":
    main()
