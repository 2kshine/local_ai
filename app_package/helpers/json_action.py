import json

def write_json(json_data, filename):
    if not filename.endswith('.json'):
        print(f"Warning@helpers.write_json :: It's recommended to use a .json extension for JSON files :: payload: {f"filename: {filename}"}")
    
    try:
        # Convert the data to a pretty-printed JSON string
        json_data_str = json.dumps(json_data, indent=4)

        # Open the file in write mode and write the string to it
        with open(filename, 'w') as file:
            file.write(json_data_str)
        
        print(f"Success@helpers.write_json :: Write Json action complete :: payload: {f"filename: {filename}"}")
        return True
    except Exception as e:
        print(f"Error@helpers.write_json :: Failed to write JSON data to :: error: {e}, payload: {f"filename: {filename}"}")
        return False
    
def read_json(json_filepath):
    try:
        # Reads a JSON file and returns its content.
        with open(json_filepath, 'r') as file:
            data = json.load(file)
        
        print(f"Success@helpers.read_json :: Successfully read JSON file :: payload: {f"json_filepath: {json_filepath}"}")
        return data
    except Exception as e:
        print(f"Error@helpers.read_json :: An error occurred while reading JSON data :: error: {e}, payload: {f"json_filepath: {json_filepath}"})
        return False