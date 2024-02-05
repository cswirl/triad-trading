import json

def load_keys_from_file():

    #filename = os.path.join(KEYS_FOLDER_PATH, 'pkeys.json')
    file_path = "../vault/pkeys.json"
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            print(f"json data from {file_path} was loaded")
            return data
    except FileNotFoundError:
        print(f"error loading json data: File '{file_path}' not found.")
    except json.JSONDecodeError:
        print(f"error decoding JSON in file '{file_path}'.")