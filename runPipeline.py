import requests
import json
import zipfile
import io
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse
from Constants import ORGANIZATION, PROJECT, personal_access_token, TGS_API_E2E_TESTS
from TestDictionary import TEST_OWNERS, TEST_SUITE_NAMES
from Utilities.fetchPipelineDataFunctions import get_build_report, get_test_run_results, get_test_logs_for_tgs
from Utilities.dataManipulationFunctions import extract_test_data, get_test_suite_name_from_test_name

# Get the build ID from the user
buildId = input("Enter the build ID: ")

# Get the build report for the provided buildId
build_report_response = get_build_report(ORGANIZATION, PROJECT, buildId)

# Initialize a dictionary to store each testRun's id and name
test_runs = {}

resultsForGroup = build_report_response["resultsForGroup"]

for testResult in resultsForGroup:
    group_by_value = testResult.get('groupByValue', {})
    id_ = group_by_value.get('id')
    name = group_by_value.get('name')
    if test_runs is not None and name is not None:
        test_runs[id_] = name


# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter('output2.xlsx', engine='openpyxl')

html_content = ""
summary_table = "<table border='1'>\n"
summary_table += "<tr><th>Test Run Name</th><th>Failure Count</th><th>Owner</th></tr>\n"

# Iterate through each test category and the individual test cases inside it
for id_, name in test_runs.items():
    # Get test run results
    test_run_result = get_test_run_results(ORGANIZATION, PROJECT, id_)

    test_run_logs = []
    # Get test logs for TGS E2Es
    if name == TGS_API_E2E_TESTS:
        test_run_logs_string = get_test_logs_for_tgs(ORGANIZATION, PROJECT, buildId)
        test_run_logs = extract_test_data(test_run_logs_string)

        # print(json.dumps(test_run_logs, indent=2))
    
    test_run_failure_count = test_run_result['count']
    
    if test_run_failure_count == 0:
        df = pd.DataFrame([[name, "SUCCEEDED"]], columns=["Test Suite", "Outcome"])
        df.to_excel(writer, sheet_name=name, index=False)
        html_content += f"Name: {name}, SUCCEEDED <br><br>"
    else:
        html_content += f"Name: {name}, ({test_run_failure_count}) <br>"
        response_array = test_run_result["value"]
        
        request_details_row_header_html = ""
        if name == TGS_API_E2E_TESTS:
            request_details_row_header_html = "<th>Request Details</th>"
        # Create html table
        html_table = "<table border='1'>\n"
        html_table += f"<tr><th>Test Suite</th><th>Serial</th><th>Name</th><th>Outcome</th><th>Error Message</th>{request_details_row_header_html}</tr>\n"

        grouped_rows = {}

        # Iterate through all test cases in this test category and group them together based on test suite
        for obj in response_array:
            storageFileName = obj['automatedTestStorage']
            automatedTestName = obj['automatedTestName']
            if name == TGS_API_E2E_TESTS:
                testSuiteDetails = get_test_suite_name_from_test_name(storageFileName, automatedTestName)
                testSuiteName = testSuiteDetails["test_suite_name"]
                testSuiteOwner = testSuiteDetails["test_suite_owner"]
            else:
                testSuiteName = TEST_SUITE_NAMES.get(storageFileName, {"name": storageFileName})["name"]
                testSuiteOwner = TEST_SUITE_NAMES.get(storageFileName, {"Owner": ""})["Owner"]
            if testSuiteName not in grouped_rows:
                grouped_rows[testSuiteName] = []
            obj['testOwner'] = testSuiteOwner
            grouped_rows[testSuiteName].append(obj)

        serial_number = 1

        for testSuiteName, rows in grouped_rows.items():
            rowspan = len(rows)  # Calculate rowspan dynamically
            new_failure_count = 0
            data = []
            for i, obj in enumerate(rows):

                failingSinceBuildId = obj['failingSince']['build']['id']
                if int(failingSinceBuildId) == int(buildId):
                    new_failure_indicator = f" ({failingSinceBuildId})"
                    new_failure_count += 1
                else:
                    new_failure_indicator = ""

                request_data = ""
                request_data_html_content = ""
                if name == TGS_API_E2E_TESTS:
                    request_data_array = [test['data'] for test in test_run_logs if test['testName'] == obj['automatedTestName']]
                    if request_data_array:
                        request_data = request_data_array[0]
                    else:
                        request_data = ""
                    request_data_html_content = f"<td>{request_data}</td>"
                    data.append([testSuiteName, f"{obj['automatedTestName']}{new_failure_indicator}", obj['outcome'], obj['errorMessage'], request_data])
                    df = pd.DataFrame(data, columns=["Test Suite", "Name", "Outcome", "Error Message", "Request Details"])
                else:
                    data.append([testSuiteName, obj['automatedTestName'], obj['outcome'], obj['errorMessage']])
                    df = pd.DataFrame(data, columns=["Test Suite", "Name", "Outcome", "Error Message"])
                
                if i == 0:
                    html_table += f"<tr><td rowspan='{rowspan}'>{testSuiteName}</td><td>{serial_number}</td><td>{obj['automatedTestName']}{new_failure_indicator}</td><td>{obj['outcome']}</td><td>{obj['errorMessage']}</td>{request_data_html_content}</tr>\n"
                else:
                    html_table += f"<tr><td>{serial_number}</td><td>{obj['automatedTestName']}{new_failure_indicator}</td><td>{obj['outcome']}</td><td>{obj['errorMessage']}</td>{request_data_html_content}</tr>\n"
                serial_number += 1
            
            summary_table += f"<tr><td>{testSuiteName}</td><td>{rowspan} ({new_failure_count} New)</td><td>{obj['testOwner']}</td></tr>\n"
            
            df.to_excel(writer, sheet_name=testSuiteName, index=False)

        html_table += "</table><br>"
        html_content += html_table

summary_table += "</table><br>"
html_content = """<style>
    table {
        width: 70%;
        margin: auto;
        border-collapse: collapse;
    }
    th, td {
        border: 1px solid black;
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
    }
    h1 {
        text-align: center;
        color: #333;
        font-family: Arial, sans-serif;
    }
    p {
        text-align: center;
        font-size: 16px;
        color: #666;
        font-family: Arial, sans-serif;
    }
    body{
        margin: 5%;
    }
</style>"""
html_content += f"<h1>E2E Validation for Build Id: '{buildId}'</h1><br><p> Please find the summary of text runs below:</p><br><br>"
html_content += summary_table

# Close the Pandas Excel writer and output the Excel file.
writer._save()

with open("output.html", "w", encoding="utf-8") as file:
    file.write(html_content)

