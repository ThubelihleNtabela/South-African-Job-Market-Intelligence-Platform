"""
Streamlit Dashboard for South African Job Market Intelligence Platform

This module creates an interactive dashboard to visualize job market data from
Azure SQL Database. It provides metrics, charts, and filters for analyzing job
listings, salaries, companies, and locations.

Run this dashboard with:
    streamlit run src/dashboard/app.py
"""

import os
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


# ============================================================================
# CONFIGURATION AND SETUP
# ============================================================================

# Configure Streamlit page
st.set_page_config(
    page_title="Job Market Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


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
    if not sql_server or not sql_database or not sql_username or not sql_password:
        raise ValueError(
            "Missing Azure SQL Database credentials in .env file. "
            "Please ensure SQL_SERVER, SQL_DATABASE, SQL_USERNAME, and SQL_PASSWORD are set."
        )
    
    return {
        "server": sql_server,
        "database": sql_database,
        "username": sql_username,
        "password": sql_password,
    }


def create_sql_connection_string(credentials):
    """
    Create a SQLAlchemy connection string for Azure SQL Database using ODBC Driver 18.
    
    Args:
        credentials (dict): Dictionary with server, database, username, password
        
    Returns:
        str: SQLAlchemy connection string using pyodbc with encoded ODBC connection
    """
    # Build the ODBC connection string with required parameters
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


@st.cache_resource
def get_database_engine():
    """
    Create and cache a SQLAlchemy engine for database connections.
    
    This function is decorated with @st.cache_resource to ensure the engine
    is created only once and reused across Streamlit reruns.
    
    Returns:
        sqlalchemy.engine.Engine: Database engine for SQL connections
    """
    credentials = load_sql_credentials()
    connection_string = create_sql_connection_string(credentials)
    engine = create_engine(connection_string)
    return engine


@st.cache_data
def load_jobs_data():
    """
    Load all jobs data from Azure SQL Database.
    
    This function is decorated with @st.cache_data to cache the results
    and avoid redundant database queries during Streamlit reruns.
    
    Returns:
        pd.DataFrame: DataFrame containing all jobs data from the jobs table
        
    Raises:
        Exception: If database connection or query fails
    """
    try:
        engine = get_database_engine()
        query = "SELECT * FROM jobs;"
        df = pd.read_sql_query(query, con=engine)
        return df
    except Exception as e:
        st.error(f"Failed to load data from Azure SQL Database: {e}")
        return None


def get_filtered_data(df, selected_category, selected_company, selected_location):
    """
    Apply filters to the jobs DataFrame.
    
    Args:
        df (pd.DataFrame): Original jobs DataFrame
        selected_category (str): Selected job category (or "All" for no filter)
        selected_company (str): Selected company (or "All" for no filter)
        selected_location (str): Selected location (or "All" for no filter)
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    # Start with the original DataFrame
    filtered_df = df.copy()
    
    # Apply category filter if selected
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]
    
    # Apply company filter if selected
    if selected_company != "All":
        filtered_df = filtered_df[filtered_df["company"] == selected_company]
    
    # Apply location filter if selected
    if selected_location != "All":
        filtered_df = filtered_df[filtered_df["location"] == selected_location]
    
    return filtered_df


def get_salary_statistics(df):
    """
    Calculate salary statistics, excluding records where salary_average = 0.
    
    Args:
        df (pd.DataFrame): Jobs DataFrame
        
    Returns:
        dict: Dictionary with average_salary and has_data flag
    """
    # Filter out records with no salary data (salary_average = 0)
    salary_data = df[df["salary_average"] > 0]["salary_average"]
    
    if len(salary_data) == 0:
        return {
            "average_salary": 0,
            "has_data": False,
        }
    
    return {
        "average_salary": salary_data.mean(),
        "has_data": True,
    }


# ============================================================================
# PAGE LAYOUT
# ============================================================================

# Page title
st.title("📊 South African Job Market Intelligence Dashboard")

# Load data from Azure SQL
try:
    df = load_jobs_data()
    
    if df is None or df.empty:
        st.error("No data available. Please ensure the database has been loaded with job data.")
        st.stop()
    
    # Display data loaded status
    st.success(f"✓ Loaded {len(df)} job listings from Azure SQL Database")
    
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()


# ============================================================================
# SIDEBAR FILTERS
# ============================================================================

st.sidebar.header("🔍 Filters")

# Create filter options
categories = sorted(df["category"].unique().tolist())
companies = sorted(df["company"].unique().tolist())
locations = sorted(df["location"].unique().tolist())

# Add "All" option to each filter
categories = ["All"] + categories
companies = ["All"] + companies
locations = ["All"] + locations

# Create sidebar filters
selected_category = st.sidebar.selectbox(
    "Select Job Category:",
    categories,
    index=0,
)

selected_company = st.sidebar.selectbox(
    "Select Company:",
    companies,
    index=0,
)

selected_location = st.sidebar.selectbox(
    "Select Location:",
    locations,
    index=0,
)

# Apply filters to data
filtered_df = get_filtered_data(df, selected_category, selected_company, selected_location)

# Display number of results after filtering
st.sidebar.info(f"📌 Showing {len(filtered_df)} job(s)")


# ============================================================================
# KEY METRICS
# ============================================================================

st.subheader("📈 Key Metrics")

# Create four columns for metrics
col1, col2, col3, col4 = st.columns(4)

# Metric 1: Total Jobs
with col1:
    total_jobs = len(filtered_df)
    st.metric("Total Jobs", total_jobs)

# Metric 2: Average Salary
with col2:
    salary_stats = get_salary_statistics(filtered_df)
    if salary_stats["has_data"]:
        avg_salary = salary_stats["average_salary"]
        st.metric("Avg Salary (R)", f"{avg_salary:,.0f}")
    else:
        st.metric("Avg Salary (R)", "N/A", delta="No salary data")

# Metric 3: Number of Companies
with col3:
    num_companies = filtered_df["company"].nunique()
    st.metric("Companies", num_companies)

# Metric 4: Number of Categories
with col4:
    num_categories = filtered_df["category"].nunique()
    st.metric("Categories", num_categories)


# ============================================================================
# CHARTS
# ============================================================================

st.subheader("📊 Visualizations")

# Create two columns for the first row of charts
col1, col2 = st.columns(2)

# Chart 1: Jobs by Category
with col1:
    st.markdown("#### Jobs by Category")
    category_jobs = filtered_df["category"].value_counts().reset_index()
    category_jobs.columns = ["Category", "Count"]
    
    if len(category_jobs) > 0:
        fig = px.bar(
            category_jobs,
            x="Category",
            y="Count",
            color="Count",
            color_continuous_scale="Blues",
            height=400,
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for this filter")

# Chart 2: Top Hiring Companies
with col2:
    st.markdown("#### Top Hiring Companies")
    company_jobs = filtered_df["company"].value_counts().head(10).reset_index()
    company_jobs.columns = ["Company", "Count"]
    
    if len(company_jobs) > 0:
        fig = px.bar(
            company_jobs,
            x="Count",
            y="Company",
            color="Count",
            color_continuous_scale="Greens",
            height=400,
            orientation="h",
        )
        fig.update_layout(showlegend=False, yaxis_autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No company data available for this filter")


# Create two columns for the second row of charts
col1, col2 = st.columns(2)

# Chart 3: Jobs by Location
with col1:
    st.markdown("#### Jobs by Location (Top 10)")
    location_jobs = filtered_df["location"].value_counts().head(10).reset_index()
    location_jobs.columns = ["Location", "Count"]
    
    if len(location_jobs) > 0:
        fig = px.bar(
            location_jobs,
            x="Location",
            y="Count",
            color="Count",
            color_continuous_scale="Oranges",
            height=400,
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No location data available for this filter")

# Chart 4: Average Salary by Category
with col2:
    st.markdown("#### Average Salary by Category")
    # Filter out records with no salary data
    salary_by_category = filtered_df[filtered_df["salary_average"] > 0].groupby("category")["salary_average"].mean().reset_index()
    salary_by_category.columns = ["Category", "Average Salary"]
    salary_by_category = salary_by_category.sort_values("Average Salary", ascending=False)
    
    if len(salary_by_category) > 0:
        fig = px.bar(
            salary_by_category,
            x="Category",
            y="Average Salary",
            color="Average Salary",
            color_continuous_scale="Reds",
            height=400,
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No salary data available for this filter")


# Full-width chart: Salary Distribution
st.markdown("#### Salary Distribution")
salary_distribution = filtered_df[filtered_df["salary_average"] > 0]["salary_average"]

if len(salary_distribution) > 0:
    fig = px.histogram(
        salary_distribution,
        nbins=30,
        title="Distribution of Average Salaries",
        labels={"value": "Salary (R)", "count": "Number of Jobs"},
        color_discrete_sequence=["#1f77b4"],
        height=400,
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No salary data available for this filter")


# ============================================================================
# DATA TABLE
# ============================================================================

st.subheader("📋 Detailed Job Listings")

# Display filtered data table with selected columns
columns_to_display = ["job_id", "title", "company", "location", "category", "salary_min", "salary_max", "salary_average"]
display_df = filtered_df[columns_to_display].copy()

# Format salary columns
display_df["salary_min"] = display_df["salary_min"].apply(lambda x: f"R {x:,.0f}" if x > 0 else "N/A")
display_df["salary_max"] = display_df["salary_max"].apply(lambda x: f"R {x:,.0f}" if x > 0 else "N/A")
display_df["salary_average"] = display_df["salary_average"].apply(lambda x: f"R {x:,.0f}" if x > 0 else "N/A")

st.dataframe(display_df, use_container_width=True, height=400)

# Option to download filtered data as CSV
csv = display_df.to_csv(index=False)
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv,
    file_name="job_market_data.csv",
    mime="text/csv",
)


# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown(
    """
    **South African Job Market Intelligence Dashboard**
    
    This dashboard provides insights into the South African job market using data from the Adzuna API.
    Data is automatically fetched, cleaned, and stored in Azure SQL Database.
    
    Last updated: Check the data ingestion schedule for latest updates.
    """
)
