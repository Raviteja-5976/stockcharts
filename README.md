# Stock Charts FastAPI Automation

A FastAPI application that automates stock chart data collection and processing.

## Features

- Automated login to StockCharts.com
- Data scanning and CSV download
- Data processing and JSON conversion
- API integration with Boomi

## Deployment

This app is configured for deployment on Render using Docker.

## Environment Variables

Set these in your Render dashboard:

- `STOCKCHARTS_USER_ID`
- `STOCKCHARTS_PASSWORD`
- `BOOMI_API_URL`
- `BOOMI_USERNAME`
- `BOOMI_PASSWORD`

## API Endpoints

- `GET /` - Health check
- `POST /run-pipeline` - Execute the full automation pipeline
