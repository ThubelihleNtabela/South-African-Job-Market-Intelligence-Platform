"""
Data Ingestion Package

This package contains modules for fetching data from various job market sources.
"""

from .adzuna_api import fetch_jobs, fetch_multiple_pages

__all__ = ["fetch_jobs", "fetch_multiple_pages"]
