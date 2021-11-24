#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

from tkinter.filedialog import askopenfilename
import csv

import requests

import keystore.keystore as keystore


def read_input_file():
    file = askopenfilename(title="Select input CSV file")
    with open(file, 'r') as input_file:
        reader = csv.DictReader(input_file, delimiter=',', skipinitialspace=True)
        fields = reader.fieldnames
        lists_out = [row for row in reader]

    return fields, lists_out


def viewer_json_generation_call(request_session, domain, project_id, experiment_id):

    generate_call = request_session.post(f"{domain}/xapi/viewer/projects/{project_id}/experiments/{experiment_id}")
    print(generate_call.status_code)


def main():
    label, domain, username, password = keystore.retrieve_entry_details()
    headers, data = read_input_file()

    project_id = input(f"Enter Project ID: ")

    with requests.Session() as request_session:
        request_session.auth = (username, password)
        for row in data:
            session_id = row[headers[0]]
            viewer_json_generation_call(request_session, domain, project_id, session_id)


if __name__ == "__main__":
    main()
