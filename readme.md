# Bluestock Fintech: Mutual Fund Analytics Platform

An end-to-end data engineering, ETL pipeline, and analytics platform built for the Bluestock Fintech Mutual Fund Capstone Project[cite: 1]. 

## Project Overview
This repository contains the data engineering infrastructure, ETL scripts, and database modeling required to process, clean, and analyze public mutual fund data from AMFI India and `mfapi.in`[cite: 1].

## Repository Structure
```text
Capstone_Submission/
├── data/
│   ├── raw/                 # Original ingested CSV datasets (01_ through 10_)[cite: 1]
│   └── processed/           # Cleaned flat-file CSV outputs[cite: 1]
├── notebooks/               # Jupyter notebooks for EDA and advanced analytics[cite: 1]
├── sql/                     # Schema DDL definitions and analytical queries[cite: 1]
├── dashboard/               # Power BI / Tableau dashboard files (.pbix)[cite: 1]
├── reports/                 # Final documentation and PDF reports[cite: 1]
├── etl_pipeline.py          # Master ETL execution script[cite: 1]
├── live_nav_fetch.py        # REST API fetcher for live NAV data[cite: 1]
├── requirements.txt         # Project dependencies[cite: 1]
└── README.md                # Project documentation