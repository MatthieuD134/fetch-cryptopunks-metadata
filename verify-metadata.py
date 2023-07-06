import os
import json

EXPORT_FOLDER = "exported_metadata"
MISSING_FILES_FILE = "missing_files.txt"
EXPORTED_IMAGE_FOLDER = "exported_images"\

def verify_metadata_integrity():
    """
    For each file in the exported folder, verify if each json file contain a name, image and attributes
    """
    missing_files = []

    # Iterate over the JSON files in the export folder
    for filename in os.listdir(EXPORT_FOLDER):
        if filename.endswith(".json"):
            file_path = os.path.join(EXPORT_FOLDER, filename)

            # Load the JSON file
            with open(file_path, "r") as file:
                try:
                    metadata = json.load(file)
                    # Check if the required fields are present
                    if "name" not in metadata or "image" not in metadata or "attributes" not in metadata:
                        missing_files.append(os.path.splitext(filename)[0])
                    else:
                        # Extract the image data from the JSON
                        image_data = metadata['image']

                        # Remove the "data:image/svg+xml;utf8," prefix from the data URL
                        encoded_image = image_data.replace('data:image/svg+xml;utf8,', '')

                        # Save the image data to a file
                        with open(f'{EXPORTED_IMAGE_FOLDER}/{os.path.splitext(filename)[0]}.svg', 'w') as file:
                            file.write(encoded_image)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON file: {filename}")

    # Save the names of missing files to a text file
    if missing_files:
        with open(MISSING_FILES_FILE, "w") as file:
            file.write("\n".join(missing_files))
        print(f"The following files are missing required fields and have been stored in {MISSING_FILES_FILE}:")
        print("\n".join(missing_files))
    else:
        print("All files contain the required fields.")

if __name__ == "__main__":
    verify_metadata_integrity()