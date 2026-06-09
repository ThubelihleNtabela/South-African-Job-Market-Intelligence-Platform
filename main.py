"""
Main entry point for the South African Job Market Intelligence Platform
"""

from src.ingestion import fetch_jobs


def main():
    """Main function to run the data ingestion pipeline"""
    print("South African Job Market Intelligence Platform started successfully.")
    
    # Fetch jobs from Adzuna API
    print("\n--- Starting Data Ingestion ---")
    jobs_data = fetch_jobs(keyword="data analyst", page=1)
    
    if jobs_data:
        print(f"\nSuccessfully fetched {len(jobs_data.get('results', []))} job listings.")
    else:
        print("\nFailed to fetch job data. Please check your credentials and internet connection.")


if __name__ == "__main__":
    main()
