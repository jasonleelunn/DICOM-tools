#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

# Script takes text file with XNAT session names (each on new line) and checks to see if they appear in a
# project specific region of the prearchive, and returns a text file with all of the timestamps of the matches

import requests
from tkinter.filedialog import asksaveasfilename, askopenfilename


def get_login_details():
    domain = input(f"Enter XNAT Domain: ")
    username = input(f"Enter Username for {domain}: ")
    password = input(f"Enter Password for {username}@{domain}: ")

    return domain, username, password


def get_xnat_session_list(domain, user, pw, project):
    sessions = requests.get(f'{domain}/data/prearchive/projects/{project}',
                            auth=(user, pw), verify=False)
    data_json = sessions.json()
    sessions_dic = {}
    for sesh in data_json['ResultSet']['Result']:
        sessions_dic[sesh['name']] = sesh['timestamp']

    return sessions_dic


def read_session_file():
    filename = askopenfilename(title="Select an Input File")
    with open(filename) as file:
        wanted_list = [line.rstrip() for line in file]

    return wanted_list


# can't seem to download data directly from prearchive with REST, at least for ROI Collections :(
def get_session(domain, user, pw):
    download = requests.get(f'{domain}/data/prearchive/projects/Unassigned/20201127_170233013',
                            auth=(user, pw), verify=False)
    print(download.status_code, download.text)

    file_path = "test_download.zip"
    with open(f"{file_path}", 'wb') as file:
        file.write(download.content)


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
    project = input(f"Enter Project ID: ")
    # project = "Unassigned"
    dom, u, pw = get_login_details()
    wanted_list = read_session_file()
    prearchive_dictionary = get_xnat_session_list(dom, u, pw, project)

    matched_keys = prearchive_dictionary.keys() & wanted_list
    result = [prearchive_dictionary[k] for k in matched_keys]

    save_output(result)


if __name__ == "__main__":
    main()
