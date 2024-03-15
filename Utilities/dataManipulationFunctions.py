import requests
import json
import zipfile
import io
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse
from TestDictionary import TEST_OWNERS, TEST_SUITE_NAMES

def extract_test_data(log_content):
    tests = {}
    current_test_name = None
    current_test = {}
    lines = log_content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith("Request Sent Timestamp:"):
            if current_test_name:
                tests[current_test_name] = current_test_data
            current_test_name = prev_line.split('|')[2]
            current_test_data = ""
        elif line.startswith("###"):
            continue
        elif line.startswith("Authorization:"):
            continue
        elif current_test_name:
            current_test_data += line + "\n"
        prev_line = line
        # Append the last test
        if current_test_name and current_test_name not in tests:             
            tests[current_test_name] = current_test_data
    return [{"testName": test_name, "data": test_data} for test_name, test_data in tests.items()]

def get_test_suite_name_from_test_name(storageFileName, test_name):
    # Gets Test suit name from the storage file name
    # For ex: "Microsoft.Teams.FirstPartyBots.Tests.E2E.Tests.Places.PlacesTest.Places_SettingsUpdate_ShouldUpdateUserLocation"
    parts = test_name.split('.')
    test_suite_name = parts[3]
    test_folder_name = parts[-2]
    test_details_from_dictionary = TEST_SUITE_NAMES.get(storageFileName, {"name": storageFileName, "Owner": "", "subTestNames": {}})

    if test_details_from_dictionary["subTestNames"]:
        test_subtest_details_from_dictionary = test_details_from_dictionary["subTestNames"].get(test_folder_name, 
        {   
            "name" : test_details_from_dictionary["name"], 
            "Owner": test_details_from_dictionary["Owner"]
        })
        test_suite_name = test_subtest_details_from_dictionary["name"]
        test_suite_owner = test_subtest_details_from_dictionary["Owner"]
    else:
        test_suite_name = test_details_from_dictionary["name"]
        test_suite_owner = test_details_from_dictionary["Owner"]

    return { "test_suite_name" : test_suite_name, "test_suite_owner": test_suite_owner }
