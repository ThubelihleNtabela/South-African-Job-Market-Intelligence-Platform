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
from datetime import datetime
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
    Create a SQLAlchemy connection string for Azure SQL Database using pymssql.
    
    Args:
        credentials (dict): Dictionary with server, database, username, password
        
    Returns:
        str: SQLAlchemy connection string using pymssql
    """
    username = quote_plus(credentials["username"])
    password = quote_plus(credentials["password"])
    server = credentials["server"]
    database = credentials["database"]

    connection_string = (
        f"mssql+pymssql://{username}:{password}@{server}:1433/{database}"
    )

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
        st.warning("Using sample dataset because Azure SQL is temporarily unavailable.")
        try:
            fallback_path = os.path.join("data", "sample", "cleaned_jobs_sample.csv")
            df = pd.read_csv(fallback_path)
            return df
        except Exception as fallback_error:
            st.error(
                f"Failed to load fallback sample dataset: {fallback_error}"
            )
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


def extract_and_count_skills(df):
    """
    Extract and count all skills from the skills column.
    
    This function:
    1. Reads the skills column from the DataFrame
    2. Splits comma-separated skills
    3. Removes "No Skills Identified" entries
    4. Counts the occurrence of each skill
    5. Returns a DataFrame sorted by count (descending)
    
    Args:
        df (pd.DataFrame): Jobs DataFrame with a 'skills' column
        
    Returns:
        pd.DataFrame: DataFrame with columns ['skill', 'count'] sorted by count descending
    """
    # Initialize dictionary to store skill counts
    skill_counts = {}
    
    # Iterate through each job's skills
    for skills_text in df["skills"]:
        # Skip empty or null values
        if not skills_text or skills_text == "No Skills Identified":
            continue
        
        # Split comma-separated skills and clean whitespace
        skills = [skill.strip() for skill in skills_text.split(",")]
        
        # Count each skill
        for skill in skills:
            if skill:  # Skip empty strings
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    # Convert to DataFrame
    if skill_counts:
        skills_df = pd.DataFrame(
            list(skill_counts.items()),
            columns=["skill", "count"]
        )
        # Sort by count in descending order
        skills_df = skills_df.sort_values("count", ascending=False).reset_index(drop=True)
    else:
        # Return empty DataFrame if no skills found
        skills_df = pd.DataFrame(columns=["skill", "count"])
    
    return skills_df


def extract_skills_by_category(df):
    """
    Extract and count skills grouped by job category.
    
    This function:
    1. Iterates through each job record
    2. Splits comma-separated skills
    3. Removes "No Skills Identified" entries
    4. Groups skills by category
    5. Counts skill occurrences per category
    
    Args:
        df (pd.DataFrame): Jobs DataFrame with 'skills' and 'category' columns
        
    Returns:
        pd.DataFrame: DataFrame with columns ['category', 'skill', 'count'] 
                     sorted by count (descending)
    """
    # Initialize list to store records
    records = []
    
    # Iterate through each job
    for _, row in df.iterrows():
        category = row.get("category", "Unknown")
        skills_text = row.get("skills", "")
        
        # Skip empty or "No Skills Identified" entries
        if not skills_text or skills_text == "No Skills Identified":
            continue
        
        # Split comma-separated skills and clean whitespace
        skills = [skill.strip() for skill in skills_text.split(",")]
        
        # Add a record for each skill
        for skill in skills:
            if skill:  # Skip empty strings
                records.append({
                    "category": category,
                    "skill": skill,
                })
    
    # Convert to DataFrame and count occurrences
    if records:
        skills_by_category = pd.DataFrame(records)
        skills_by_category = skills_by_category.groupby(
            ["category", "skill"]
        ).size().reset_index(name="count")
        skills_by_category = skills_by_category.sort_values(
            "count", ascending=False
        ).reset_index(drop=True)
    else:
        # Return empty DataFrame if no records
        skills_by_category = pd.DataFrame(columns=["category", "skill", "count"])
    
    return skills_by_category


def extract_skills_by_location(df):
    """
    Extract and count skills grouped by location.
    
    This function:
    1. Iterates through each job record
    2. Splits comma-separated skills
    3. Removes "No Skills Identified" entries
    4. Groups skills by location
    5. Counts skill occurrences per location
    
    Args:
        df (pd.DataFrame): Jobs DataFrame with 'skills' and 'location' columns
        
    Returns:
        pd.DataFrame: DataFrame with columns ['location', 'skill', 'count']
                     sorted by count (descending)
    """
    # Initialize list to store records
    records = []
    
    # Iterate through each job
    for _, row in df.iterrows():
        location = row.get("location", "Unknown")
        skills_text = row.get("skills", "")
        
        # Skip empty or "No Skills Identified" entries
        if not skills_text or skills_text == "No Skills Identified":
            continue
        
        # Split comma-separated skills and clean whitespace
        skills = [skill.strip() for skill in skills_text.split(",")]
        
        # Add a record for each skill
        for skill in skills:
            if skill:  # Skip empty strings
                records.append({
                    "location": location,
                    "skill": skill,
                })
    
    # Convert to DataFrame and count occurrences
    if records:
        skills_by_location = pd.DataFrame(records)
        skills_by_location = skills_by_location.groupby(
            ["location", "skill"]
        ).size().reset_index(name="count")
        skills_by_location = skills_by_location.sort_values(
            "count", ascending=False
        ).reset_index(drop=True)
    else:
        # Return empty DataFrame if no records
        skills_by_location = pd.DataFrame(columns=["location", "skill", "count"])
    
    return skills_by_location


# ============================================================================
# PAGE LAYOUT
# ============================================================================

# Page header
header_col, header_meta = st.columns([3, 1])
with header_col:
    st.title("📊 South African Job Market Intelligence Dashboard")
    st.markdown(
        "Modern portfolio-ready analytics for South African job market demand, skills, and salary trends."
    )
with header_meta:
    last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.metric("🕒 Last Updated", last_refresh)

st.divider()

# Load data from Azure SQL
try:
    df = load_jobs_data()
    
    if df is None or df.empty:
        st.error("No data available. Please ensure the database has been loaded with job data.")
        st.stop()
    
    st.success(f"✓ Loaded {len(df)} job listings from Azure SQL Database")
    
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

st.markdown(
    "This dashboard is powered by Azure SQL Database and refreshed through a Python ETL pipeline that ingests Adzuna data, processes it with Pandas, and stores cleaned job market data for analytics."
)

st.divider()

# ============================================================================
# SIDEBAR FILTERS
# ============================================================================

st.sidebar.title("Dashboard Filters")
st.sidebar.markdown(
    "Use these filters to explore the job market by category, company, and location. Set filters to 'All' to return to the full dataset."
)
st.sidebar.markdown("---")

# Create filter options
categories = sorted(df["category"].dropna().unique().tolist())
companies = sorted(df["company"].dropna().unique().tolist())
locations = sorted(df["location"].dropna().unique().tolist())

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

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Reset filters:** choose 'All' for category, company, or location to clear the filter and return to the full dataset."
)

# Apply filters to data
filtered_df = get_filtered_data(df, selected_category, selected_company, selected_location)

st.sidebar.info(f"📌 Showing {len(filtered_df)} job(s)")

# Ensure salary distribution and skills metrics are available for tabs
salary_stats = get_salary_statistics(filtered_df)
salary_distribution = filtered_df[filtered_df["salary_average"] > 0]["salary_average"]
skills_df = extract_and_count_skills(filtered_df)

# ============================================================================
# DASHBOARD TABS
# ============================================================================

overview_tab, skills_tab, salary_tab, architecture_tab, company_location_tab, data_tab = st.tabs(
    ["Overview", "Skills", "Salary", "Architecture", "Companies & Locations", "Data Table"]
)

with overview_tab:
    st.subheader("Overview")
    st.markdown("High-level metrics and market snapshot for the filtered job listings.")

    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric("Total Jobs", len(filtered_df))
    with kpi2:
        st.metric(
            "Average Salary",
            f"R {salary_stats['average_salary']:,.0f}" if salary_stats["has_data"] else "N/A",
        )
    with kpi3:
        st.metric("Unique Companies", filtered_df["company"].nunique())

    kpi4, kpi5, kpi6 = st.columns(3)
    with kpi4:
        st.metric("Job Categories", filtered_df["category"].nunique())
    with kpi5:
        st.metric("Unique Skills", len(skills_df))
    with kpi6:
        st.metric("Total Skill Mentions", skills_df["count"].sum() if len(skills_df) > 0 else 0)

    st.divider()
    st.markdown("#### Market Snapshot")
    category_jobs = filtered_df["category"].value_counts().head(10).reset_index()
    category_jobs.columns = ["Category", "Count"]

    if len(category_jobs) > 0:
        fig = px.bar(
            category_jobs,
            x="Count",
            y="Category",
            orientation="h",
            template="plotly_white",
            color="Count",
            color_continuous_scale="Blues",
            height=450,
            labels={"Count": "Job Listings", "Category": "Category"},
        )
        fig.update_layout(showlegend=False, yaxis_autorange="reversed", margin=dict(l=120, r=20, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No category data available for the selected filters.")

with skills_tab:
    st.subheader("Skills Demand")
    st.markdown("Deep dive into the most sought-after technical skills in the current dataset.")

    skill_kpi1, skill_kpi2, skill_kpi3 = st.columns(3)
    with skill_kpi1:
        st.metric("Unique Skills Detected", len(skills_df))
    with skill_kpi2:
        st.metric("Total Skill Mentions", skills_df["count"].sum() if len(skills_df) > 0 else 0)
    with skill_kpi3:
        if len(skills_df) > 0:
            top_skill = skills_df.iloc[0]["skill"]
            top_skill_count = skills_df.iloc[0]["count"]
            st.metric("Top Skill", top_skill, delta=f"{top_skill_count} mentions")
        else:
            st.metric("Top Skill", "N/A", delta="No skills data")

    st.divider()
    st.markdown("#### Most In-Demand Skills")
    if len(skills_df) > 0:
        top_skills = skills_df.head(15)
        fig = px.bar(
            top_skills,
            x="count",
            y="skill",
            orientation="h",
            template="plotly_white",
            color="count",
            color_continuous_scale="Viridis",
            height=500,
            labels={"count": "Mentions", "skill": "Skill"},
        )
        fig.update_layout(showlegend=False, yaxis_autorange="reversed", margin=dict(l=140, r=20, t=40, b=30))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(
            "No skill data found for the selected filters. Try choosing All filters or another category/location."
        )

    st.divider()
    categories_col, locations_col = st.columns(2)

    with categories_col:
        st.markdown("#### Top Skills by Job Category")
        skills_by_cat = extract_skills_by_category(filtered_df)
        if len(skills_by_cat) > 0:
            top_10_skills = skills_by_cat.groupby("skill")["count"].sum().nlargest(10).index.to_list()
            skills_by_cat_filtered = skills_by_cat[skills_by_cat["skill"].isin(top_10_skills)]
            fig = px.bar(
                skills_by_cat_filtered,
                x="count",
                y="skill",
                color="category",
                orientation="h",
                template="plotly_white",
                barmode="group",
                height=500,
                labels={"count": "Mentions", "skill": "Skill", "category": "Category"},
            )
            fig.update_layout(showlegend=True, yaxis_autorange="reversed", margin=dict(l=140, r=20, t=40, b=30))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                "No skill data found for the selected filters. Try choosing All filters or another category/location."
            )

    with locations_col:
        st.markdown("#### Top Skills by Location")
        skills_by_loc = extract_skills_by_location(filtered_df)
        if len(skills_by_loc) > 0:
            top_10_skills = skills_by_loc.groupby("skill")["count"].sum().nlargest(10).index.to_list()
            skills_by_loc_filtered = skills_by_loc[skills_by_loc["skill"].isin(top_10_skills)]
            fig = px.bar(
                skills_by_loc_filtered,
                x="count",
                y="skill",
                color="location",
                orientation="h",
                template="plotly_white",
                barmode="group",
                height=500,
                labels={"count": "Mentions", "skill": "Skill", "location": "Location"},
            )
            fig.update_layout(showlegend=True, yaxis_autorange="reversed", margin=dict(l=140, r=20, t=40, b=30))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                "No skill data found for the selected filters. Try choosing All filters or another category/location."
            )

with salary_tab:
    st.subheader("Salary Insights")
    st.markdown("Analyze compensation trends across the filtered dataset.")

    salary_jobs = filtered_df[filtered_df["salary_average"] > 0]
    salary_col1, salary_col2, salary_col3 = st.columns(3)
    with salary_col1:
        st.metric("Average Salary", f"R {salary_stats['average_salary']:,.0f}" if salary_stats["has_data"] else "N/A")
    with salary_col2:
        st.metric("Jobs with Salary Data", len(salary_jobs))
    with salary_col3:
        st.metric("Salary Data Coverage", f"{len(salary_jobs)}/{len(filtered_df)}")

    st.divider()
    st.markdown("#### Average Salary by Category")
    salary_by_category = salary_jobs.groupby("category")["salary_average"].mean().reset_index()
    salary_by_category.columns = ["Category", "Average Salary"]
    salary_by_category = salary_by_category.sort_values("Average Salary", ascending=False).head(10)
    if len(salary_by_category) > 0:
        fig = px.bar(
            salary_by_category,
            x="Average Salary",
            y="Category",
            orientation="h",
            template="plotly_white",
            color="Average Salary",
            color_continuous_scale="Reds",
            height=450,
            labels={"Average Salary": "Average Salary (R)", "Category": "Category"},
        )
        fig.update_layout(showlegend=False, yaxis_autorange="reversed", margin=dict(l=120, r=20, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No salary category data available for the selected filters.")

    st.divider()
    st.markdown("#### Salary Distribution")
    if len(salary_distribution) > 0:
        fig = px.histogram(
            salary_distribution,
            nbins=30,
            template="plotly_white",
            color_discrete_sequence=["#636efa"],
            height=450,
            labels={"value": "Salary (R)", "count": "Job Count"},
        )
        fig.update_layout(showlegend=False, margin=dict(l=40, r=20, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No salary distribution data available for the selected filters.")

with architecture_tab:
    st.subheader("Architecture")
    st.markdown("Understand the end-to-end data pipeline powering this dashboard.")

    st.markdown(
        """
        **Adzuna API**  
        Ingest job listings and metadata from the Adzuna service.

        **↓**

        **Python ETL Pipeline**  
        Clean, enrich, and transform raw job data into analytics-ready records.

        **↓**

        **Azure Blob Storage**  
        Stage raw JSON files and store artifacts for traceability.

        **↓**

        **Azure SQL Database**  
        Persist cleaned job records for querying and dashboard analytics.

        **↓**

        **Streamlit Dashboard**  
        Display interactive hiring insights, salary trends, and skill demand.
        """
    )

with company_location_tab:
    st.subheader("Companies & Locations")
    st.markdown("Visualize the leading companies and geographies hiring in the current dataset.")

    companies_col, locations_col = st.columns(2)
    with companies_col:
        st.markdown("#### Top Hiring Companies")
        invalid_companies = {"Unknown", "No Company Listed", "None", ""}
        company_clean = filtered_df["company"].fillna("").astype(str).str.strip()
        valid_company_mask = ~company_clean.isin(invalid_companies)
        company_jobs = filtered_df.loc[valid_company_mask, "company"].value_counts().head(10).reset_index()
        company_jobs.columns = ["Company", "Count"]
        if len(company_jobs) > 0:
            fig = px.bar(
                company_jobs,
                x="Count",
                y="Company",
                orientation="h",
                template="plotly_white",
                color="Count",
                color_continuous_scale="Greens",
                height=450,
                labels={"Count": "Job Listings", "Company": "Company"},
            )
            fig.update_layout(showlegend=False, yaxis_autorange="reversed", margin=dict(l=120, r=20, t=40, b=40))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No company data available for the selected filters.")

    with locations_col:
        st.markdown("#### Top Locations")
        location_jobs = filtered_df["location"].value_counts().head(10).reset_index()
        location_jobs.columns = ["Location", "Count"]
        if len(location_jobs) > 0:
            fig = px.bar(
                location_jobs,
                x="Count",
                y="Location",
                orientation="h",
                template="plotly_white",
                color="Count",
                color_continuous_scale="Oranges",
                height=450,
                labels={"Count": "Job Listings", "Location": "Location"},
            )
            fig.update_layout(showlegend=False, yaxis_autorange="reversed", margin=dict(l=120, r=20, t=40, b=40))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No location data available for the selected filters.")

with data_tab:
    st.subheader("Detailed Job Listings")
    st.markdown("Download the filtered dataset and inspect key fields used by the dashboard.")

    columns_to_display = [
        "job_id",
        "title",
        "company",
        "location",
        "category",
        "salary_min",
        "salary_max",
        "salary_average",
        "skills",
    ]
    display_df = filtered_df[columns_to_display].copy()
    display_df["salary_min"] = display_df["salary_min"].apply(lambda x: f"R {x:,.0f}" if x > 0 else "N/A")
    display_df["salary_max"] = display_df["salary_max"].apply(lambda x: f"R {x:,.0f}" if x > 0 else "N/A")
    display_df["salary_average"] = display_df["salary_average"].apply(lambda x: f"R {x:,.0f}" if x > 0 else "N/A")

    st.dataframe(display_df, use_container_width=True, height=520)
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name="job_market_data.csv",
        mime="text/csv",
    )

st.divider()
st.markdown(
    """
    Created by Thubelihle Ntabela
    Azure Data Engineering Portfolio Project
    """
)
