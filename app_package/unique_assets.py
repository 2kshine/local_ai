from app_package.helpers.directory_helper import TRACK_ASSETS
import json
import os

def asset_tracker(asset, filename):
    try:
        with open(os.path.join(TRACK_ASSETS, f"{filename}.json"), 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data[asset]
    except FileNotFoundError:
        print(f"The file path does not exist.")
    except json.JSONDecodeError:
        print(f"The file contains invalid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def asset_keeper(asset, filename, asset_filename):
    try:
        # Load existing data
        file_path = os.path.join(TRACK_ASSETS, f"{filename}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        else:
            data = {}

        # Ensure the asset key exists in the data
        if asset not in data:
            data[asset] = []

        # Add the new asset filename to the list
        if asset_filename not in data[asset]:
            data[asset].append(asset_filename)

        # Write the updated data back to the JSON file
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        
        print(f"Asset '{asset_filename}' added successfully to '{asset}' in '{filename}'.")

    except FileNotFoundError:
        print(f"The file path does not exist.")
    except json.JSONDecodeError:
        print(f"The file contains invalid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")    