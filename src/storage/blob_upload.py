"""
Azure Blob Storage Upload Module

This module provides functionality to upload cleaned job data to Azure Blob Storage.
It handles credential loading, connection management, and file uploads.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient


def load_azure_credentials():
    """
    Load Azure Blob Storage credentials from the .env file.
    
    Returns:
        tuple: (connection_string, container_name)
        
    Raises:
        ValueError: If required Azure credentials are missing in .env
    """
    # Load environment variables from .env file
    load_dotenv()
    
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME")
    
    # Check if both credentials are present
    if not connection_string:
        raise ValueError(
            "Missing AZURE_STORAGE_CONNECTION_STRING in .env file. "
            "Please add it to proceed with Azure Blob Storage uploads."
        )
    
    if not container_name:
        raise ValueError(
            "Missing AZURE_BLOB_CONTAINER_NAME in .env file. "
            "Please add it to proceed with Azure Blob Storage uploads."
        )
    
    return connection_string, container_name


def check_local_file_exists(file_path):
    """
    Check if the local file exists.
    
    Args:
        file_path (str): Path to the local file
        
    Returns:
        bool: True if file exists, False otherwise
        
    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(
            f"Local file not found: {file_path}. "
            "Please run the data cleaning step first."
        )
    
    return True


def upload_file_to_blob(file_path, blob_path, connection_string, container_name):
    """
    Upload a local file to Azure Blob Storage.
    
    This function creates a BlobServiceClient, connects to the specified container,
    and uploads the file. If the blob already exists, it will be overwritten.
    
    Args:
        file_path (str): Local file path to upload
        blob_path (str): Path inside the container where the file will be stored
        connection_string (str): Azure Storage connection string
        container_name (str): Azure Blob Storage container name
        
    Returns:
        dict: Dictionary containing blob name and container name
        
    Raises:
        Exception: If upload fails
    """
    try:
        # Create a BlobServiceClient from the connection string
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        
        # Get the container client
        container_client = blob_service_client.get_container_client(container_name)
        
        # Get the blob client for the specific blob
        blob_client = container_client.get_blob_client(blob_path)
        
        # Upload the file (overwrite if exists)
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        return {
            "blob_name": blob_path,
            "container_name": container_name,
        }
    
    except Exception as e:
        raise Exception(f"Failed to upload file to Azure Blob Storage: {e}")


def upload_cleaned_jobs_to_blob():
    """
    Main function to upload the cleaned jobs CSV to Azure Blob Storage.
    
    This function:
    1. Loads Azure credentials from .env
    2. Checks that the local cleaned_jobs.csv file exists
    3. Connects to Azure Blob Storage
    4. Uploads the file to processed/cleaned_jobs.csv
    5. Overwrites the blob if it already exists
    6. Prints the blob path after successful upload
    
    Returns:
        bool: True if upload was successful, False otherwise
    """
    try:
        print("\n--- Starting Azure Blob Storage Upload ---")
        
        # Step 1: Load Azure credentials
        print("Step 1: Loading Azure Blob Storage credentials...")
        connection_string, container_name = load_azure_credentials()
        print("  ✓ Credentials loaded successfully")
        
        # Step 2: Define local and blob paths
        local_file_path = "data/processed/cleaned_jobs.csv"
        blob_path = "processed/cleaned_jobs.csv"
        
        # Step 3: Check that local file exists
        print("Step 2: Checking local file existence...")
        check_local_file_exists(local_file_path)
        print(f"  ✓ Found: {local_file_path}")
        
        # Step 4: Upload file to Azure Blob Storage
        print("Step 3: Uploading to Azure Blob Storage...")
        result = upload_file_to_blob(
            file_path=local_file_path,
            blob_path=blob_path,
            connection_string=connection_string,
            container_name=container_name,
        )
        
        # Step 5: Print results
        print("\n--- Azure Upload Complete ---")
        print(f"Container:    {result['container_name']}")
        print(f"Blob path:    {result['blob_name']}")
        print(f"✓ File uploaded successfully to Azure Blob Storage")
        
        return True
    
    except ValueError as e:
        # Handle missing credentials error
        print(f"\n❌ Configuration Error: {e}")
        return False
    
    except FileNotFoundError as e:
        # Handle missing local file error
        print(f"\n❌ File Error: {e}")
        return False
    
    except Exception as e:
        # Handle upload errors
        print(f"\n❌ Upload Error: {e}")
        return False
