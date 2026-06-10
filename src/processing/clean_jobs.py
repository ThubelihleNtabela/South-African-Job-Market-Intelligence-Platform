"""
Data Cleaning Module for Job Listings

This module provides functionality to clean and process raw job data from the Adzuna API.
It handles data extraction, transformation, and deduplication to produce clean datasets.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime


def get_latest_raw_file():
    """
    Find and return the path to the latest raw JSON file in data/raw/.
    
    Returns:
        Path: Path object pointing to the most recently modified JSON file
        
    Raises:
        FileNotFoundError: If no JSON files are found in data/raw/
    """
    raw_data_dir = Path("data/raw")
    
    # Find all JSON files in the raw data directory
    json_files = list(raw_data_dir.glob("*.json"))
    
    if not json_files:
        raise FileNotFoundError(
            f"No JSON files found in {raw_data_dir}. "
            "Please run the ingestion step first."
        )
    
    # Return the most recently modified file
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    return latest_file


def load_raw_data(file_path):
    """
    Load raw job data from a JSON file.
    
    Args:
        file_path (Path): Path to the raw JSON file
        
    Returns:
        list: List of job records from the API response
        
    Raises:
        json.JSONDecodeError: If the file is not valid JSON
        KeyError: If the 'results' key is missing from the JSON
    """
    with open(file_path, "r") as f:
        data = json.load(f)
    
    # Extract the results list from the API response
    results = data.get("results", [])
    
    return results


def extract_and_clean_fields(results):
    """
    Extract relevant fields from raw job data and create a DataFrame.
    
    This function handles nested JSON fields and performs initial cleaning
    by extracting display names from nested objects.
    
    Args:
        results (list): List of raw job records from the API
        
    Returns:
        pd.DataFrame: DataFrame with extracted fields
    """
    cleaned_data = []
    
    for job in results:
        # Extract fields, handling nested structures and missing values
        record = {
            "job_id": job.get("id"),
            "title": job.get("title", ""),
            "company": job.get("company", {}).get("display_name", "Unknown") 
                if isinstance(job.get("company"), dict) else "Unknown",
            "location": job.get("location", {}).get("display_name", "") 
                if isinstance(job.get("location"), dict) else "",
            "category": job.get("category", {}).get("label", "") 
                if isinstance(job.get("category"), dict) else "",
            "description": job.get("description", ""),
            "created": job.get("created"),
            "salary_min": job.get("salary_min", 0),
            "salary_max": job.get("salary_max", 0),
            "redirect_url": job.get("redirect_url", ""),
        }
        cleaned_data.append(record)
    
    # Create DataFrame from the extracted records
    df = pd.DataFrame(cleaned_data)
    
    return df


def clean_data(df):
    """
    Perform data cleaning operations on the job listings DataFrame.
    
    Operations include:
    - Removing duplicate jobs by job_id
    - Filling missing company values with "Unknown"
    - Filling missing salary values with 0
    - Converting created field to datetime
    - Stripping extra spaces from text columns
    - Creating salary_average column
    
    Args:
        df (pd.DataFrame): Raw DataFrame with job listings
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    # Store initial record count for reporting
    initial_count = len(df)
    
    # Remove duplicate jobs using job_id
    df = df.drop_duplicates(subset=["job_id"], keep="first")
    
    # Calculate number of duplicates removed
    duplicates_removed = initial_count - len(df)
    
    # Fill missing company values with "Unknown"
    df["company"] = df["company"].fillna("Unknown")
    df["company"] = df["company"].replace("", "Unknown")
    
    # Fill missing salary values with 0
    df["salary_min"] = df["salary_min"].fillna(0)
    df["salary_max"] = df["salary_max"].fillna(0)
    
    # Convert created field to datetime
    df["created"] = pd.to_datetime(df["created"], errors="coerce")
    
    # Strip extra spaces from text columns
    text_columns = ["title", "company", "location", "category", "description"]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].str.strip()
    
    # Create salary_average column
    df["salary_average"] = (df["salary_min"] + df["salary_max"]) / 2
    
    return df, duplicates_removed


def save_cleaned_data(df, output_path="data/processed/cleaned_jobs.csv"):
    """
    Save the cleaned DataFrame to a CSV file.
    
    Args:
        df (pd.DataFrame): Cleaned job listings DataFrame
        output_path (str): Path where the CSV file will be saved
        
    Returns:
        Path: Path object pointing to the saved file
    """
    # Create the processed data directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the cleaned data to CSV
    df.to_csv(output_path, index=False)
    
    return Path(output_path)


def clean_jobs():
    """
    Main function to orchestrate the entire data cleaning pipeline.
    
    This function:
    1. Loads the latest raw JSON file
    2. Extracts relevant fields from the data
    3. Performs data cleaning operations
    4. Saves the cleaned data to CSV
    5. Prints statistics about the cleaning process
    
    Returns:
        dict: Dictionary containing cleaning statistics and file path
    """
    try:
        print("\n--- Starting Data Cleaning ---")
        
        # Step 1: Find and load the latest raw file
        print("Step 1: Loading latest raw data file...")
        latest_file = get_latest_raw_file()
        results = load_raw_data(latest_file)
        raw_count = len(results)
        print(f"  - Loaded {raw_count} raw records from: {latest_file}")
        
        # Step 2: Extract and clean fields
        print("Step 2: Extracting and transforming fields...")
        df = extract_and_clean_fields(results)
        
        # Step 3: Perform data cleaning
        print("Step 3: Performing data cleaning operations...")
        df, duplicates_removed = clean_data(df)
        cleaned_count = len(df)
        
        # Step 4: Save cleaned data
        print("Step 4: Saving cleaned data...")
        output_file = save_cleaned_data(df)
        
        # Step 5: Print statistics
        print("\n--- Data Cleaning Complete ---")
        print(f"Raw record count:        {raw_count}")
        print(f"Cleaned record count:    {cleaned_count}")
        print(f"Duplicates removed:      {duplicates_removed}")
        print(f"Output file location:    {output_file}")
        
        return {
            "raw_count": raw_count,
            "cleaned_count": cleaned_count,
            "duplicates_removed": duplicates_removed,
            "output_file": str(output_file),
        }
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None
    
    except Exception as e:
        print(f"Error during data cleaning: {e}")
        return None
