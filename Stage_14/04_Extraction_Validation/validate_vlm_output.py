#!/usr/bin/env python3
import json, sys
def validate(file_path):
    with open(file_path) as f: data = json.load(f)
    for el in data.get('elements', []):
        d = el.get('dimensions', {})
        for k in ['length', 'width', 'depth']:
            if d.get(k, {}).get('value', 0) <= 0:
                print(f"FAILED: {k} must be > 0")
                sys.exit(1)
    print("VALIDATION PASSED")
if __name__ == '__main__': validate(sys.argv[1])
