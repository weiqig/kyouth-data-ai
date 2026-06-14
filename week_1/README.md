## Project Description

This project implements a local ETL (Extract, Transform, Load) pipeline designed to process raw job listing data into a clean, structured format stored in a relational database (jobs.db).

The pipeline follows a simplified Medallion Architecture, organizing data into progressive layers of quality:

- Bronze Layer (Extract): Raw data ingestion from the 0_source directory.

- Silver Layer (Transform): Data cleaning and processing, including removal of HTML noise and normalization of fields.

- Gold Layer (Load): Structured and validated data loaded into a relational database.
Objective

The goal is to build a robust and idempotent pipeline that:

    - Extracts raw job data
    - Cleans and processes it into readable text
    - Structures it into a consistent schema
    - Loads it into jobs.db
    - Displays formatted database information from jobs.db


## ETL pipeline and Medallion Architecture overview

The pipeline follows a standard ETL pipeline:

[SOURCE] → [EXTRACT] → [CLEAN / PROCESS] → [LOAD] → [DATABASE]

Also known as a medallion architecture, which is a layered data design pattern that organizes data into Bronze, Silver, and Gold layers to progressively improve quality, structure, and usability to ensure reliability, and performance as it flows through the system. It is not tied to a specific technology and can be implemented on platforms like Databricks, Snowflake, or Hadoop-based systems

### Key Components

Extractor (Bronze):
- Captures raw, unprocessed data to be processed
- Reads raw files from 0_source
- Handles ingestion in a consistent format

Processing Layer (Silver):
- Performs data cleaning, validation, and transformation
- Cleans HTML from descriptions
- Normalizes text and fields
- Extracts relevant metadata (e.g., job title, company)

Storage Layer (Gold):
- provides high quality datasets ready for use
- Writes structured data into jobs.db
- Ensures schema consistency



## Instructions
1. Environment Setup

    Must include a .python-version file with the following content:

        3.14

    Include the required dependencies:

        uv 0.8.*
        ruff 0.15.*
        pydantic 2.13.*

    Install dependencies:
    ```sh
    uv sync
    ```

2. Run the Pipeline

    To execute each pipline separately:
    ```sh
    uv run python main.py <command>
    ```

    available commands include:
    - **ingest** - extracts *.html from *.mhtml files from ( 0_source > 1_bronze )
    - **process** - process and clean html data into .json (1_bronze > 2_silver)
    - **load** - load json data into jobs.db (2_silver > 3_gold)
    - **profile** - provide a detailed output of database information (3_gold)

    To execute the full ETL pipeline:
    ```sh
    uv run python main.py all
    ```

    This will:
    - Extract raw data from 0_source/
    - Clean and process the data
    - Load the results into jobs.db
    - display information about data stored in database

## Technical Reflections

### Module 1: The Extractor (Medallion & Lakehouses)
**Reflection:** Why is it useful to keep the original raw HTML files instead of directly inserting processed data into the database? What problems become easier to debug or recover from?

Having the original file can help in comparing any parsing errors or mismatches in processed data, and also recover from data corruption or errors during database transactions by rebuilding the processed data from the original raw HTML files. Ultimately, storing raw HTML allows for better pipeline stability in terms of robustness and allowing for easier debugging and recovery processes.


### Day 2: Treatment Plant (ETL vs ELT & Scale)
**Reflection:** Why do cloud systems prefer loading raw data first before cleaning it (ELT)? What problems happen when processing files sequentially, and how does distributed processing help?

Cloud systems prefer ELT because storing raw data first preserves the original data, allows transformations to be changed later, and takes advantage of scalable cloud storage and computing resources. Processing files sequentially can be slow, especially when dealing with large datasets, because each file must wait for the previous one to finish. Distributed processing solves this by processing multiple files in parallel across several machines, reducing execution time and improving scalability and reliability


### Module 3: The Blueprint & The Vault (Storage & Contracts)
**Reflection:** What should happen if an important field like `job_title` disappears? Why fail early instead of silently inserting `nulls` into DB? How does `INSERT OR IGNORE` help prevent duplicate records?

If an important field like job_title disappears, the system should fail early and raise an error or perform a transaction rollback to prevent inserting incomplete data into the database. Failing early helps detect data quality issues immediately, preventing invalid records from being stored and making troubleshooting easier. If null values are inserted silently, errors may go unnoticed and affect downstream analysis or applications albeit depending on whether or not the field itself should hold null values or not.

INSERT OR IGNORE helps prevent duplicate records by checking the table's primary key (source_id). If a record with the same source_id already exists, the insert operation is ignored instead of creating a duplicate entry or causing the process to fail. This ensures data integrity while allowing the pipeline to run safely on repeated data loads.

### Module 4: The QA Inspector & Orchestrator (Orchestration & DAGs)
**Reflection:** What happens if `processor.py` crashes halfway? How are automated orchestration tools more reliable than manual retries with Python scripts?

If processor.py crashes halfway through processing HTML files, some JSON files may be created while others are missing, leaving the pipeline in an incomplete state. This can lead to inconsistent data and may require checking which files were successfully processed before rerunning the script. Without proper tracking, manually rerunning the script could result in duplicate work or missed files. The program can crash and cause downtime as well if errors aren't handled properly, potentially leading to financial losses as well.

Automated orchestration tools are more reliable because they can monitor tasks, detect failures, automatically retry failed steps, and keep track of execution status. Unlike manual retries with Python scripts, orchestration tools provide logging, scheduling, dependency management, and recovery mechanisms, reducing the risk of human error and making large-scale data pipelines more robust.