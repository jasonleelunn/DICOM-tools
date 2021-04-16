#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import requests
from tkinter.filedialog import asksaveasfilename
import getpass
import json


def get_login_details():

    with open("login_details.json", 'r') as details_file:
        details = json.load(details_file)

    domain = details['domain']
    # domain = input(f"Enter XNAT Domain: ")
    username = details['username']
    # username = input(f"Enter Username for {domain}: ")
    password = getpass.getpass(prompt=f"Enter Password for {username}@{domain}: ")

    return domain, username, password


def get_patient_list(session, domain, user, pw):

    project = input(f"Enter Project ID: ")
    patients = session.get(f'{domain}/data/projects/{project}/subjects',
                            auth=(user, pw), verify=False)
    patient_json = patients.json()
    patient_label_list = []
    [patient_label_list.append(pati['label']) for pati in patient_json['ResultSet']['Result']]

    return project, patient_label_list


def session_edit(sessions):
    mod_sessions = []
    scanner_name = input("Enter scanner name: ")
    for session in sessions:
        mod_session = session[0][:16] + scanner_name
        mod_sessions.append((mod_session, session[1]))

    return mod_sessions


def save_output(lines):
    filename = asksaveasfilename(defaultextension=".csv")
    if not filename:
        print("File creation cancelled...")
        raise SystemExit
    else:
        with open(filename, 'w', newline='') as file:
            for item in lines:
                # file.write(f"{item[0], item[1]}\n")
                file.write(','.join(str(x) for x in item) + '\n')
        print(f"File Created!\nFile is located at '{filename}'")


def main(session):
    dom, u, pw = get_login_details()
    project, patient_list = get_patient_list(session, dom, u, pw)
    modality = input("Modality of session: ")

    sessions_label_dic = []
    for patient in patient_list:
        if modality:
            sessions = session.get(f'{dom}/data/projects/{project}'
                                    f'/subjects/{patient}/experiments?modality={modality}',
                                    auth=(u, pw), verify=False)
        else:
            sessions = session.get(f'{dom}/data/projects/{project}'
                                   f'/subjects/{patient}/experiments',
                                   auth=(u, pw), verify=False)
        sessions_json = sessions.json()
        [sessions_label_dic.append((sesh['label'], patient)) for sesh in sessions_json['ResultSet']['Result']]

    # sessions_label_dic = session_edit(sessions_label_dic)
    print(f"Number of sessions found: {len(sessions_label_dic)}")
    save_output(sessions_label_dic)


if __name__ == "__main__":
    with requests.Session() as requests_session:
        main(requests_session)
