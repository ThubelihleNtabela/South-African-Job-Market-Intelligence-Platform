"""
Azure SQL Database Loader Module

This module provides functionality to load cleaned job data into Azure SQL Database.
It handles credential loading, connection management, and data loading operations.
"""

import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


def load_sql_credentials():
    """
    Load Azure SQL Database credentials from the .env file.
    
    Returns:
        dict: Dictionary containing SQL server, database, username, and password
        
    Raises:
        ValueError: If any required SQL credentials are missing in .env
    """
    # Load environment variables from .env file
    load_dotenv()
    
    sql_server = os.getenv("SQL_SERVER")
    sql_database = os.getenv("SQL_DATABASE")
    sql_username = os.getenv("SQL_USERNAME")
    sql_password = os.getenv("SQL_PASSWORD")
    
    # Check if all credentials are present
    if not sql_server:
        raise ValueError(
            "Missing SQL_SERVER in .env file. "
            "Please add it to proceed with Azure SQL Database loading."
        )
    
    if not sql_database:
        raise ValueError(
            "Missing SQL_DATABASE in .env file. "
            "Please add it to proceed with Azure SQL Database loading."
        )
    
    if not sql_username:
        raise ValueError(
            "Missing SQL_USERNAME in .env file. "
            "Please add it to proceed with Azure SQL Database loading."
        )
    
    if not sql_password:
        raise ValueError(
            "Missing SQL_PASSWORD in .env file. "
            "Please add it to proceed with Azure SQL Database loading."
        )
    
    return {
        "server": sql_server,
        "database": sql_database,
        "username": sql_username,
        "password": sql_password,
    }


def check_csv_file_exists(file_path):
    """
    Check if the cleaned CSV file exists.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        bool: True if file exists
        
    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {file_path}. "
            "Please run the data cleaning step first."
        )
    
    return True


def read_csv_to_dataframe(file_path):
    """
    Read the cleaned CSV file into a pandas DataFrame.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: DataFrame containing the cleaned job data
        
    Raises:
        Exception: If CSV reading fails
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise Exception(f"Failed to read CSV file: {e}")


def create_sql_connection_string(credentials):
    """
    Create a SQLAlchemy connection string for Azure SQL Database using ODBC Driver 18.
    
    This function creates a properly formatted connection string with the following
    security and connection parameters:
    - DRIVER: ODBC Driver 18 for SQL Server
    - SERVER: Azure SQL Server hostname
    - DATABASE: Database name
    - UID: Username (from credentials)
    - PWD: Password (from credentials)
    - Encrypt: Enable connection encryption (yes)
    - TrustServerCertificate: Verify server certificate (no)
    - Connection Timeout: 30 seconds
    
    The connection string is URL-encoded using urllib.parse.quote_plus for safe
    transmission to SQLAlchemy.
    
    Args:
        credentials (dict): Dictionary with server, database, username, password
        
    Returns:
        str: SQLAlchemy connection string using pyodbc with encoded ODBC connection
    """
    # Build the ODBC connection string with all required parameters
    odbc_connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={credentials['server']};"
        f"DATABASE={credentials['database']};"
        f"UID={credentials['username']};"
        f"PWD={credentials['password']};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    # URL-encode the connection string for safe use in SQLAlchemy URL
    encoded_connection_string = quote_plus(odbc_connection_string)
    
    # Create the SQLAlchemy connection string using the encoded ODBC string
    connection_string = f"mssql+pyodbc:///?odbc_connect={encoded_connection_string}"
    
    return connection_string


def load_dataframe_to_sql(df, connection_string, table_name="jobs"):
    """
    Load a pandas DataFrame into an Azure SQL Database table.
    
    This function:
    - Creates a connection to the database
    - Loads the DataFrame into the specified table
    - Replaces the table if it already exists
    - Includes data type inference for proper SQL mapping
    
    Args:
        df (pd.DataFrame): DataFrame to load
        connection_string (str): SQLAlchemy connection string
        table_name (str): Name of the table to create/replace (default: "jobs")
        
    Returns:
        int: Number of records loaded
        
    Raises:
        Exception: If database connection or load fails
    """
    try:
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        
        # Load the DataFrame to SQL table (replace existing table)
        df.to_sql(table_name, con=engine, if_exists="replace", index=False)
        
        # Return the number of records loaded
        record_count = len(df)
        return record_count
    
    except Exception as e:
        raise Exception(f"Failed to load data into SQL table: {e}")


def load_jobs_to_sql():
    """
    Main function to load cleaned job data into Azure SQL Database.
    
    This function orchestrates the entire SQL loading process:
    1. Loads Azure SQL credentials from .env
    2. Checks that the cleaned_jobs.csv file exists
    3. Reads the CSV into a DataFrame
    4. Creates a connection string for Azure SQL
    5. Loads the DataFrame into the jobs table
    6. Replaces existing table data
    7. Prints loading statistics
    
    Returns:
        bool: True if load was successful, False otherwise
    """
    try:
        print("\n--- Starting Azure SQL Database Load ---")
        
        # Step 1: Load SQL credentials
        print("Step 1: Loading Azure SQL Database credentials...")
        credentials = load_sql_credentials()
        print("  ✓ Credentials loaded successfully")
        
        # Step 2: Define file path
        csv_file_path = "data/processed/cleaned_jobs.csv"
        
        # Step 3: Check that CSV file exists
        print("Step 2: Checking CSV file existence...")
        check_csv_file_exists(csv_file_path)
        print(f"  ✓ Found: {csv_file_path}")
        
        # Step 4: Read CSV into DataFrame
        print("Step 3: Reading CSV into DataFrame...")
        df = read_csv_to_dataframe(csv_file_path)
        print(f"  ✓ Loaded {len(df)} records from CSV")
        
        # Step 5: Create SQL connection string
        print("Step 4: Creating database connection...")
        connection_string = create_sql_connection_string(credentials)
        
        # Step 6: Load DataFrame to SQL
        print("Step 5: Loading data into Azure SQL Database...")
        table_name = "jobs"
        record_count = load_dataframe_to_sql(df, connection_string, table_name)
        
        # Step 7: Print results
        print("\n--- Azure SQL Load Complete ---")
        print(f"Records loaded:    {record_count}")
        print(f"Database name:     {credentials['database']}")
        print(f"Table name:        {table_name}")
        print(f"✓ Data loaded successfully to Azure SQL Database")
        
        return True
    
    except ValueError as e:
        # Handle missing credentials error
        print(f"\n❌ Configuration Error: {e}")
        return False
    
    except FileNotFoundError as e:
        # Handle missing CSV file error
        print(f"\n❌ File Error: {e}")
        return False
    
    except Exception as e:
        # Handle loading errors
        print(f"\n❌ Load Error: {e}")
        return False
