#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

"""
Get the contents of an XNAT project in a csv format for the Anonymisation Tool
"""

import csv
from tkinter.filedialog import asksaveasfilename

import requests

import keystore.keystore as keystore


def get_subject_list(domain, project_id):
    request = constant_session.get(f'{domain}/data/projects/{project_id}/subjects')
    subject_json = request.json()
    subject_label_list = []
    [subject_label_list.append(subject['label']) for subject in subject_json['ResultSet']['Result']]

    return subject_label_list


def get_sessions_for_subject(domain, project_id, subject):
    request = constant_session.get(f'{domain}/data/projects/{project_id}/subjects/{subject}/experiments')
    experiments_json = request.json()
    experiments_label_list = []
    [experiments_label_list.append(exp['label']) for exp in experiments_json['ResultSet']['Result']]

    return experiments_label_list


def create_lines(lines, project_id, subject_session_items):
    subject = subject_session_items[0]
    sessions = subject_session_items[1]
    for session in sessions:
        line = [
            project_id,
            session,
            subject,
            "1900-01-01",
            project_id,
            subject,
            subject,
            "#ALL"
        ]
        lines.append(line)
    return lines


def build_csv(lines):
    # filename = "../../test_output.csv"
    filename = asksaveasfilename(defaultextension=".csv")
    if not filename:
        print("CSV File creation cancelled...")
    else:
        with open(filename, 'w', newline='') as file:
            write = csv.writer(file, delimiter=',')
            write.writerows(lines)
        print(f"CSV Created!\nFile is located at '{filename}'")


def main():
    label, domain, username, password = keystore.retrieve_entry_details()
    project_id = input("Enter Project ID: ")

    constant_session.auth = (username, password)

    subject_session_dict = {}

    subject_list = get_subject_list(domain, project_id)
    subject_list.sort()

    for subject in subject_list:
        session_list = get_sessions_for_subject(domain, project_id, subject)
        subject_session_dict[subject] = session_list

    lines = []

    for subject_data in subject_session_dict.items():
        lines = create_lines(lines, project_id, subject_data)

    build_csv(lines)


if __name__ == '__main__':
    with requests.Session() as constant_session:
        main()
