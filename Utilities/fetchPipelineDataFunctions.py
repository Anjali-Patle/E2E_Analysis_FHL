import requests
import json
import zipfile
import io
import base64
from datetime import datetime
from urllib.parse import urlparse
from Constants import headers, base64_token

def get_build_report(organization, project, buildId):
    get_build_report_url = f"https://vstmr.dev.azure.com/{organization}/{project}/_apis/testresults/resultdetailsbybuild?buildId={buildId}&groupBy=TestRun"

    try:
        response = requests.get(get_build_report_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(f"Failed to fetch test runs for the provided build: {err}") from None
    return response.json()

def get_test_run_results(organization, project, testRunId):
    get_test_run_results_url = f"https://dev.azure.com/{organization}/{project}/_apis/test/Runs/{testRunId}/results?outcomes=Failed,Aborted&api-version=7.1-preview.6"

    try:
        response = requests.get(get_test_run_results_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(f"Failed to fetch test run results: {err}") from None
    return response.json()

def get_test_logs_for_tgs(organization, project, buildId):
    get_test_logs_url = f"https://dev.azure.com/{organization}/{project}/_apis/build/builds/{buildId}/artifacts?artifactName=TeamsGraphDotNetTestLogs&api-version=7.1-preview.5"

    request_headers = {
        "Content-Type": "application/json, application/zip",
        "Authorization": f"Basic {base64_token}",
        "Accept": "application/json, application/zip"
    }
    
    try:
        response = requests.get(get_test_logs_url, headers=request_headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(f"Failed to fetch test run logs: {err}") from None
    
    download_url = response.json()['resource']['downloadUrl']
    log_file = requests.get(download_url, headers=request_headers)

    zip_file = io.BytesIO(log_file.content)
    data = ""
    with zipfile.ZipFile(zip_file, 'r') as z:
        # Loop over the names of the files in the zip file
        for filename in z.namelist():
            if filename != "KeyVaultClient.log" and filename != "TenantConfiguration.log":
                # Open each file
                with z.open(filename) as f:
                    # Read the file's contents
                    data += f.read().decode('utf-8', errors='ignore')
    return data
