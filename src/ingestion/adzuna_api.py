"""
Adzuna API Ingestion Module

This module handles fetching job data from the Adzuna South Africa API.
It loads API credentials from the .env file and provides functionality to
retrieve job listings based on keywords.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv


def load_api_credentials():
    """
    Load Adzuna API credentials from the .env file.

    Returns:
        tuple: (app_id, app_key)

    Raises:
        ValueError: If ADZUNA_APP_ID or ADZUNA_APP_KEY are missing in .env
    """
    # Load environment variables from .env file
    load_dotenv()

    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    # Check if both credentials are present
    if not app_id or not app_key:
        raise ValueError("Missing ADZUNA_APP_ID or ADZUNA_APP_KEY in .env file")

    return app_id, app_key


def fetch_jobs(keyword="data analyst", page=1):
    """
    Fetch job listings from the Adzuna South Africa API.

    This function connects to the Adzuna API, retrieves job data based on
    the provided keyword, and saves the raw response as a JSON file.

    Args:
        keyword (str): Job keyword to search for (default: "data analyst")
        page (int): Page number for pagination (default: 1)

    Returns:
        dict: The API response containing job data, or None if an error occurs

    Raises:
        ValueError: If API credentials are missing
        requests.exceptions.RequestException: If the API request fails
    """
    try:
        # Load API credentials
        app_id, app_key = load_api_credentials()

        # Print status message
        print("Fetching jobs from Adzuna API...")

        # Adzuna API base URL for South Africa
        base_url = f"https://api.adzuna.com/v1/api/jobs/za/search/{page}"

        # Prepare request parameters
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": 20,
            "what": keyword,
        }

        # Make the API request with timeout
        response = requests.get(base_url, params=params, timeout=10)

        # Check if the response status code is successful
        if response.status_code != 200:
            raise requests.exceptions.RequestException(
                f"API returned status code {response.status_code}: {response.text}"
            )

        # Parse the JSON response
        data = response.json()

        # Get the number of jobs returned
        jobs_count = len(data.get("results", []))
        print(f"Number of jobs returned: {jobs_count}")

        # Create the raw data directory if it doesn't exist
        raw_data_dir = Path("data/raw")
        raw_data_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"adzuna_jobs_{timestamp}.json"
        file_path = raw_data_dir / filename

        # Save the raw API response as formatted JSON
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

        # Print the raw file location
        print(f"Raw file location: {file_path}")

        return data

    except ValueError as e:
        # Handle missing credentials error
        print(f"Error: {e}")
        return None

    except requests.exceptions.ConnectionError:
        # Handle connection errors
        print("Error: Failed to connect to the Adzuna API. Check your internet connection.")
        return None

    except requests.exceptions.Timeout:
        # Handle timeout errors
        print("Error: API request timed out. Please try again.")
        return None

    except requests.exceptions.RequestException as e:
        # Handle other API-related errors
        print(f"Error: API request failed - {e}")
        return None

    except json.JSONDecodeError:
        # Handle JSON parsing errors
        print("Error: Failed to parse API response as JSON.")
        return None

    except IOError as e:
        # Handle file writing errors
        print(f"Error: Failed to save the raw data file - {e}")
        return None

    except Exception as e:
        # Handle any other unexpected errors
        print(f"Error: An unexpected error occurred - {e}")
        return None
