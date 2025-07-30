from fastapi import FastAPI
import random
import time
import os
import json
import glob
import pandas as pd
import requests
from playwright.sync_api import sync_playwright
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

app = FastAPI()

def human_sleep():
    time.sleep(random.uniform(1, 5))

def run_scan(page, script_text, filename):
    print(f"📝 Running scan for: {filename}")
    page.goto("https://stockcharts.com/def/servlet/ScanUI")
    human_sleep()

    safe_script = json.dumps(script_text)
    page.evaluate(f"""
        () => {{
            let editor = window.ace.edit("clauses-ace");
            editor.setValue({safe_script}, -1);
        }}
    """)
    human_sleep()

    with page.expect_popup() as popup_info:
        page.click('input#runScan')
    popup = popup_info.value
    human_sleep()

    with popup.expect_download() as download_info:
        popup.click('button#download-csv')
    download = download_info.value
    download.save_as(filename)
    print(f"✅ CSV Downloaded: {filename}")
    human_sleep()

def merge_csvs_to_json(output_file="merged_output.json"):
    csv_files = glob.glob("*.csv")
    merged_data = {}

    for csv_file in csv_files:
        df = pd.read_csv(csv_file, keep_default_na=False)
        df = df.replace("", None)
        key = os.path.splitext(os.path.basename(csv_file))[0]
        merged_data[key] = df.to_dict(orient="records")

    with open(output_file, "w") as f:
        json.dump(merged_data, f, indent=4)

    print(f"✅ All CSVs merged into '{output_file}'")

    for csv_file in csv_files:
        try:
            os.remove(csv_file)
            print(f"🗑️ Deleted '{csv_file}'")
        except Exception as e:
            print(f"⚠️ Error deleting '{csv_file}': {e}")

    return merged_data  # Return merged data for response

def boomi_api_push(data):
    url = os.getenv("BOOMI_API_URL")
    username = os.getenv("BOOMI_USERNAME")
    password = os.getenv("BOOMI_PASSWORD")

    print("🔁 Sending POST request to Boomi API...")
    response = requests.post(
        url,
        json=data,
        auth=HTTPBasicAuth(username, password),
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        print("✅ Data pushed to Boomi API successfully.")
    else:
        print(f"❌ Failed to push data. Status: {response.status_code}, Response: {response.text}")

def run_pipeline_process():
    print("🚀 Starting pipeline process...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Headed mode for visibility
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("🌐 Navigating to StockCharts login...")
        page.goto("https://stockcharts.com/login/index.php")
        human_sleep()

        print("🔐 Filling login form...")
        page.fill('input[name="form_UserID"]', os.getenv("STOCKCHARTS_USER_ID"))
        human_sleep()

        page.fill('input[name="form_UserPassword"]', os.getenv("STOCKCHARTS_PASSWORD"))
        human_sleep()

        page.keyboard.press("Enter")
        print("⏳ Waiting for login to complete...")
        time.sleep(5)

        print("⚙️ Running scans...")
        run_scan(page, "[favorites list is 34]\nRank by daily chande trend meter", "daily.csv")
        run_scan(page, "[favorites list is 34]\nRank by weekly chande trend meter", "weekly.csv")
        run_scan(page, "[favorites list is 34]\nRank by month chande trend meter", "monthly.csv")

        browser.close()

        print("📦 Merging CSVs...")
        merged_data = merge_csvs_to_json()

        print("📤 Pushing to Boomi...")
        boomi_api_push(merged_data)

        print("🎉 All tasks completed successfully.")
        return merged_data

# Health check
@app.get("/")
def root():
    return {"status": "ok", "message": "FastAPI is running."}

# ✅ GET endpoint that performs the pipeline and returns the data
@app.get("/run-pipeline")
def run_pipeline():
    try:
        data = run_pipeline_process()
        return {"status": "success", "message": "Pipeline completed.", "data": data}
    except Exception as e:
        print("❌ Exception occurred in /run-pipeline:")
        traceback.print_exc()
        return {"status": "error", "message": str(e) or "Unknown error occurred"}
