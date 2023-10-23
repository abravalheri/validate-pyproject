#!/usr/bin/env python3

import argparse
import json


def convert_tree(tree: dict[str, object]) -> None:
    for key, value in list(tree.items()):
        match key, value:
            case "$$description", list():
                tree["description"] = " ".join(value)
                del tree["$$description"]
            case "$id", str():
                del tree["$id"]
            case _, dict():
                convert_tree(value)
            case _, list():
                for item in value:
                    if isinstance(item, dict):
                        convert_tree(item)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("schema", help="JSONSchema to convert")
    args = parser.parse_args()

    with open(args.schema, encoding="utf-8") as f:
        schema = json.load(f)

    convert_tree(schema)
    schema["$id"] = "https://json.schemastore.org/setuptools.json"

    print(json.dumps(schema, indent=2))
