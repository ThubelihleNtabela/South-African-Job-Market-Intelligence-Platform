"""
Main entry point for the South African Job Market Intelligence Platform

This is the primary entry point for the ETL pipeline that:
1. Fetches jobs from Adzuna API
2. Cleans raw job data
3. Saves cleaned CSV for further processing
4. Uploads cleaned CSV to Azure Blob Storage
"""

from src.ingestion import fetch_jobs
from src.processing.clean_jobs import clean_jobs
from src.storage.blob_upload import upload_cleaned_jobs_to_blob


def main():
    """
    Main function to run the complete ETL pipeline.
    
    The pipeline consists of four steps:
    1. Fetch: Retrieve raw job data from Adzuna API
    2. Clean: Process and clean the raw data
    3. Save: Store cleaned data in CSV format
    4. Upload: Upload cleaned CSV to Azure Blob Storage
    """
    print("=" * 70)
    print("South African Job Market Intelligence Platform")
    print("=" * 70)
    
    # STEP 1: Fetch jobs from Adzuna API
    print("\n[STEP 1] Fetching jobs from Adzuna API...")
    jobs_data = fetch_jobs(keyword="data analyst", page=1)
    
    if not jobs_data:
        print("\n❌ Failed to fetch job data. Please check your credentials and internet connection.")
        return False
    
    jobs_count = len(jobs_data.get('results', []))
    print(f"✓ Successfully fetched {jobs_count} job listings.")
    
    # STEP 2: Clean raw job data
    print("\n[STEP 2] Cleaning raw job data...")
    cleaning_result = clean_jobs()
    
    if not cleaning_result:
        print("\n❌ Failed to clean job data.")
        return False
    
    print("✓ Data cleaning completed successfully.")
    
    # STEP 3: Save cleaned CSV (already done in clean_jobs function)
    print("\n[STEP 3] Cleaned CSV saved to data/processed/cleaned_jobs.csv")
    print(f"✓ File location: {cleaning_result['output_file']}")
    
    # STEP 4: Upload cleaned CSV to Azure Blob Storage
    print("\n[STEP 4] Uploading cleaned CSV to Azure Blob Storage...")
    upload_success = upload_cleaned_jobs_to_blob()
    
    if not upload_success:
        print("\n⚠️  Warning: Azure upload skipped or failed. Check your Azure credentials.")
        print("   The local CSV file has been saved successfully.")
    else:
        print("✓ Upload to Azure Blob Storage completed successfully.")
    
    print("\n" + "=" * 70)
    print("✓ ETL Pipeline completed successfully!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    main()
