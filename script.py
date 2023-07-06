import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

API_KEY = os.getenv("ALCHEMY_API_KEY")
CONTRACT_ADDRESS = "0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB"
BATCH_SIZE = 100
MAX_NFTS = 10000
EXPORT_FOLDER = "exported_metadata"
START_TOKEN_FILE = "start_token.txt"
INACCESSIBLE_NFTS_FILE = "inaccessible_nft_ids.txt"
MISSING_FILES_FILE = "missing_files.txt"

def check_metadata_integrity(tokenId: int):
    """
    Check the integrity of the metadata for a given tokenId.
    """
    filename = f"{EXPORT_FOLDER}/{tokenId}.json"
    if not os.path.exists(filename):
        return False

    with open(filename, "r") as file:
        try:
            metadata = json.load(file)
            if "name" not in metadata or "image" not in metadata or "attributes" not in metadata:
                return False
            else:
                return True
        except json.JSONDecodeError:
            return False

def int_to_hex_signed_twos_complement(n):
    """
    Convert a positive integer to a signed two's complement hexadecimal representation.
    """
    if(n == 0):
        return "0x00"

    # Ensure that n is a positive integer
    if not isinstance(n, int) or n < 0:
        raise ValueError("Input must be a positive integer.")

    # Convert n to its hexadecimal representation
    hex_string = hex(n)[2:]

    # Ensure the hexadecimal string has an even number of characters
    if len(hex_string) % 2 != 0:
        hex_string = "0" + hex_string

    # Add the "0x" prefix
    hex_string = "0x" + hex_string

    return hex_string

def fetch_nfts_metadata(start_token: int):
    """
    Fetch NFT metadata from the API.
    """
    url = f"https://eth-mainnet.g.alchemy.com/nft/v2/{API_KEY}/getNFTsForCollection"
    params = {
        "contractAddress": CONTRACT_ADDRESS,
        "withMetadata": "true",
        "startToken": int_to_hex_signed_twos_complement(start_token),
        "limit": str(BATCH_SIZE)
    } if start_token > 0 else {
        "contractAddress": CONTRACT_ADDRESS,
        "withMetadata": "true",
        "limit": str(BATCH_SIZE)
    }

    response = requests.get(url, params=params)

    print(params)

    try:
        response_json = response.json()
        return response_json["nfts"]
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return []

def save_metadata_file(metadata, nft_id: int):
    """
    Save NFT metadata to a file.
    """
    filename = f"{EXPORT_FOLDER}/{nft_id}.json"
    with open(filename, "w") as file:
        json.dump(metadata, file, indent=2)

def save_start_token(start_token):
    """
    Save the tokenId to start with on next loop to a file.
    """
    with open(START_TOKEN_FILE, "w") as file:
        file.write(str(start_token))

def load_start_token():
    """
    Load the tokenId to start with from a file.
    """
    if os.path.exists(START_TOKEN_FILE):
        with open(START_TOKEN_FILE, "r") as file:
            return int(file.read())
    else:
        return 0
    
def save_inaccessible_nft_ids(nft_ids: list[int]):
    """
    Save inaccessible NFT IDs to a file.
    """
    # Convert the list of integers to a list of strings
    nft_ids_str = [str(nft_id) for nft_id in nft_ids]

    with open(INACCESSIBLE_NFTS_FILE, "w") as file:
        file.write("\n".join(nft_ids_str))

def load_inaccessible_nft_ids():
    """
    Load inaccessible NFT IDs from a file.
    """
    nft_ids = []
    if os.path.exists(INACCESSIBLE_NFTS_FILE):
        with open(INACCESSIBLE_NFTS_FILE, "r") as file:
            nft_ids_str = file.read().split("\n")
            # Convert the list of strings to a list of integers
            nft_ids += [int(nft_id) for nft_id in nft_ids_str if nft_id]



    if os.path.exists(MISSING_FILES_FILE):
        with open(MISSING_FILES_FILE, "r") as file:
            nft_ids_str = file.read().split("\n")
            # Convert the list of strings to a list of integers
            nft_ids += [int(nft_id) for nft_id in nft_ids_str if nft_id]

    return nft_ids

def find_missing_nft_id(inaccessible_token_ids):
    """
    Find the next missing NFT ID to fetch.
    """
    exported_ids = set()
    for filename in os.listdir(EXPORT_FOLDER):
        if filename.endswith(".json"):
            nft_id = int(filename[:-5])  # Remove the file extension
            exported_ids.add(nft_id)
    for nft_id in range(MAX_NFTS):
        if nft_id not in exported_ids:
            # Check if the NFT ID is burnt
            if nft_id in inaccessible_token_ids:
                continue
            return nft_id
    return None

# Fetch and save NFTs metadata in batch
def fetch_and_save_nfts_metadata():
    """
    Fetch and save NFT metadata.
    """
    # Create the export folder if it doesn't exist
    if not os.path.exists(EXPORT_FOLDER):
        os.makedirs(EXPORT_FOLDER)

    start_token = load_start_token() # 0 by default
    nft_count = len(os.listdir(EXPORT_FOLDER)) # 0 by default
    inaccessible_token_ids = load_inaccessible_nft_ids() # Empty by default

    print(f"Starting from token #{int_to_hex_signed_twos_complement(start_token)}")
    print(f"Resuming with NFT count: {nft_count}")

    # Fetch and save NFTs metadata
    while nft_count < MAX_NFTS:
        nfts_metadata = fetch_nfts_metadata(start_token)
        if not nfts_metadata:
            print("No metadata received. Exiting...")
            break

        for nft_metadata in nfts_metadata:
            nft_id_hex = nft_metadata["id"]["tokenId"][2:]
            nft_id = int(nft_id_hex, 16)

            # check if the metadata file already exists
            if os.path.exists(f"{EXPORT_FOLDER}/{nft_id}.json"):
                print(f"Metadata for NFT #{int_to_hex_signed_twos_complement(nft_id)} already exists. Skipping...")
                continue

            save_metadata_file(nft_metadata["metadata"], nft_id)
            nft_count += 1
            print(f"Saved metadata for NFT #{int_to_hex_signed_twos_complement(nft_id)} ({nft_count}/{MAX_NFTS} - {len(inaccessible_token_ids)} inaccessible NFTs)")

            if nft_count + len(inaccessible_token_ids) >= MAX_NFTS :
                print("Maximum NFTs limit reached. Exiting...")
                break

        missing_nft_id = find_missing_nft_id(inaccessible_token_ids)

        print(f"Missing NFT ID: {missing_nft_id}, {int_to_hex_signed_twos_complement(missing_nft_id) if missing_nft_id is not None else None}")
        if missing_nft_id is None:
            print("No missing NFT ID found. Exiting...")
            break
        
        if missing_nft_id == start_token:
            print("Adding missing NFT ID to inaccessible NFT IDs list.")
            inaccessible_token_ids.append(start_token)
            save_inaccessible_nft_ids(inaccessible_token_ids)
        
        start_token = missing_nft_id
        save_start_token(start_token)

        if nft_count + len(inaccessible_token_ids)  >= MAX_NFTS:
            print("Maximum NFTs limit reached. Exiting...")
            break

        time.sleep(1)  # Add a 1-second delay between API calls

# Fetch remaining inaccessible NFTs metadata, one by one, with a different API endpoint: "getNFTMetadata"
def fetch_remaining_nfts_metadata():
    """
    Fetch and save metadata for remaining inaccessible NFTs.
    """
    inaccessible_token_ids = load_inaccessible_nft_ids() # Empty by default

    print(f"Inaccessible NFT count: {len(inaccessible_token_ids)}")

    nft_count = 0

    for nft_id in inaccessible_token_ids:
        # check if the metadata file already exists
        if check_metadata_integrity(nft_id):
            print(f"Metadata for NFT #{nft_id} already exists. Skipping...")
            nft_count += 1
            continue
        
        url = f"https://eth-mainnet.g.alchemy.com/nft/v2/{API_KEY}/getNFTMetadata"
        params = {
            "contractAddress": CONTRACT_ADDRESS,
            "tokenId": nft_id # for this api endpoint the token id is an integer
        }

        response = requests.get(url, params=params)

        print(params)

        try:
            response_json = response.json()
            metadata = response_json["metadata"]
            save_metadata_file(metadata, nft_id)
            nft_count += 1
            print(f"Saved metadata for NFT #{nft_id} ({nft_count}/{len(inaccessible_token_ids)} inaccessible NFTs)")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            break

        time.sleep(1)  # Add a 1-second delay between API calls


if __name__ == "__main__":
    # exit if API_KEY is None
    if API_KEY is None:
        print("API key is not set. Exiting...")
        exit()

    fetch_and_save_nfts_metadata()
    fetch_remaining_nfts_metadata()