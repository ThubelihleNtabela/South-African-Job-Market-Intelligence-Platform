"""
Database module for Azure SQL Database operations
"""

from .sql_loader import load_jobs_to_sql

__all__ = ["load_jobs_to_sql"]
