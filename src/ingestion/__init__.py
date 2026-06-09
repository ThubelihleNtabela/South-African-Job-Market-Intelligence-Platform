"""
Data Ingestion Package

This package contains modules for fetching data from various job market sources.
"""

from .adzuna_api import fetch_jobs

__all__ = ["fetch_jobs"]
