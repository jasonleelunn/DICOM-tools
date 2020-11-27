#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import requests
from tkinter.filedialog import asksaveasfilename


def get_login_details():

    # domain = input(f"Enter XNAT Domain: ")
    # username = input(f"Enter Username for {domain}: ")
    # password = input(f"Enter Password for {username}@{domain}: ")

    domain = 'http://xnatdev.xnat.org'
    username = 'admin'
    password = 'TCIABigMemes'

    return domain, username, password


def get_patient_list(domain, user, pw):

    # project = input(f"Enter Project ID: ")
    project = "TEST_UPLOAD"
    patients = requests.get(f'{domain}/data/projects/{project}/subjects',
                            auth=(user, pw), verify=False)
    patient_json = patients.json()
    patient_label_list = []
    [patient_label_list.append(pati['label']) for pati in patient_json['ResultSet']['Result']]

    return project, patient_label_list


def save_output(lines):
    filename = asksaveasfilename(defaultextension=".txt")
    if not filename:
        print("File creation cancelled...")
        raise SystemExit
    else:
        with open(filename, 'w', newline='') as file:
            for item in lines:
                file.write("%s\n" % item)
        print(f"File Created!\nFile is located at '{filename}'")


def main():
    dom, u, pw = get_login_details()
    project, patient_list = get_patient_list(dom, u, pw)

    sessions_label_list = []
    for patient in patient_list:
        sessions = requests.get(f'{dom}/data/projects/{project}'
                                f'/subjects/{patient}/experiments',
                                auth=(u, pw), verify=not False)
        sessions_json = sessions.json()
        [sessions_label_list.append(sesh['label']) for sesh in sessions_json['ResultSet']['Result']]

    save_output(sessions_label_list)


if __name__ == "__main__":
    main()
