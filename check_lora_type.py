# usage: python check_lora_type.py [folder_path] --sort
import os
import sys
import json
import shutil

SAFETENSORS_EXT = ".safetensors"
METADATA_KEY = "__metadata__"
MODULE_KEY = "ss_network_module"


class SafeTensorsException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class SafeTensorsFile:
    @staticmethod
    def get_header_from_file(filename: str) -> dict:
        try:
            with open(filename, "rb") as f:
                b8 = f.read(8)  # read header size
                headerlen = int.from_bytes(b8, 'little', signed=False)

                if headerlen == 0:
                    raise SafeTensorsException(f"{filename} header size is 0")

                hdrbuf = f.read(headerlen)
                header = json.loads(hdrbuf)
                return header.get(METADATA_KEY, {})
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            return {}


def is_readable(file_path: str) -> bool:
    return os.access(file_path, os.R_OK)


def extract_metadata(folder_path: str = None, sort_files=False) -> dict:
    folder_path = os.path.abspath(folder_path or os.getcwd())
    module_mapping = {}

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith(SAFETENSORS_EXT):
                file_path = os.path.join(root, file_name)

                if not is_readable(file_path):
                    print(f"Cannot read file {file_path}")
                    continue

                metadata = SafeTensorsFile.get_header_from_file(file_path)

                if MODULE_KEY not in metadata:
                    print(f"'{MODULE_KEY}' not found in metadata for file: {file_path}")
                    print("Metadata content:", metadata)
                else:
                    module_type = metadata[MODULE_KEY]
                    module_mapping[file_path] = module_type

                    # Sort file into the appropriate directory if --sort argument is provided
                    if sort_files:
                        target_directory = os.path.join(folder_path, module_type)
                        if not os.path.exists(target_directory):
                            os.makedirs(target_directory)
                        shutil.move(file_path, os.path.join(target_directory, file_name))

    return module_mapping


if __name__ == "__main__":
    folder_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
    sort_files = "--sort" in sys.argv

    module_mapping = extract_metadata(folder_path, sort_files)

    for file_path, module_type in module_mapping.items():
        print(f"{os.path.basename(file_path)} - {module_type}")
