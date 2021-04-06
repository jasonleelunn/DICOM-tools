#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import requests
from tkinter.filedialog import askopenfilename
import csv
import getpass


def read_input_file():
    file = askopenfilename(title="Select input CSV file")
    with open(file, 'r') as input_file:
        reader = csv.DictReader(input_file, delimiter=',', skipinitialspace=True)
        fields = reader.fieldnames
        lists_out = [row for row in reader]

    return fields, lists_out


def get_login_details():

    domain = input(f"Enter XNAT Domain: ")
    username = input(f"Enter Username for {domain}: ")
    password = getpass.getpass(prompt=f"Enter Password for {username}@{domain}: ")

    return domain, username, password


def viewer_json_generation_call(request_session, domain, project_id, experiment_id):

    generate_call = request_session.post(f"{domain}/xapi/viewer/projects/{project_id}/experiments/{experiment_id}")
    print(generate_call.status_code)


def main():
    domain, username, password = get_login_details()
    headers, data = read_input_file()

    project_id = input(f"Enter Project ID: ")

    with requests.Session() as request_session:
        request_session.auth = (username, password)
        for row in data:
            session_id = row['session_id']
            viewer_json_generation_call(request_session, domain, project_id, session_id)


if __name__ == "__main__":
    main()
