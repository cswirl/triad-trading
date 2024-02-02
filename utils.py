import json
import pickle
import os
from datetime import datetime

TRADE_RESULT_FOLDER_PATH = 'trade_results'
DATA_FOLDER_PATH = 'data'
LOGS_FOLDER_PATH = 'logs'

# """
#     Save to File
# """

def save_json_to_file(data, folder_path, filename):
    file_path = filepath_today_folder(folder_path, filename)
    try:
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"json data has been saved to {file_path}")
    except Exception as e:
        print(f"error saving json data to {file_path}: {e}")


def save_text_file(data, folder_path, file_name):
    file_path = filepath_today_folder(folder_path, file_name)
    try:
        # Save the text data to the file
        with open(file_path, 'w') as text_file:
            text_file.write(data)
        print(f"Text data saved successfully to: {file_path}")

    except Exception as e:
        print(f"error saving text data to {file_path}: {e}")

### HELPER FUNCTIONS

def load_json_file(folder_path, filename):
    file_path = filepath_today_folder(folder_path, filename)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            print(f"json data from {file_path} was loaded")
            return data
    except FileNotFoundError:
        print(f"error loading json data: File '{file_path}' not found.")
    except json.JSONDecodeError:
        print(f"error decoding JSON in file '{file_path}'.")

def filepath_today_folder(folder_path, filename):
    # Get the current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    #folder_path = folder_path + current_date
    folder_path = os.path.join(folder_path, current_date)

    # Create the directory if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Construct the full file path including the current date
    file_path = os.path.join(folder_path, filename)

    return file_path
