#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

# Script takes csv file with XNAT session names and anonymous patient ID's (each on new line),
# checks to see if they appear in a project specific region of the prearchive, and can then copy and anonymise
# the files found

import os
import shutil
import subprocess
import datetime
import csv
import re
import requests
from tkinter.filedialog import askopenfilename
import getpass
import json
from progress.bar import Bar
import pydicom


class FancyBar(Bar):
    # message = 'Loading'
    # fill = '*'
    suffix = '%(percent).2f%% - %(eta)ds'


def get_login_details():

    with open("login_details.json", 'r') as details_file:
        details = json.load(details_file)
    domain = details['domain']
    username = details['username']
    # domain = input(f"Enter XNAT Domain: ")
    # username = input(f"Enter Username for {domain}: ")
    password = getpass.getpass(f"Enter Password for {username}@{domain}: ")

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
    with open(filename, 'r') as file:
        wanted_list = dict(csv.reader(file, delimiter=','))
        # wanted_list = [line.rstrip() for line in file]
    return wanted_list


def copy_data(prearchive_path, info_dict, project_id, number_of_files):
    script_path = askopenfilename(title="Choose an anonymisation profile")

    with FancyBar('Extracting data from prearchive... ', max=number_of_files) as bar:
        for count, (anon_id, timestamp) in enumerate(info_dict.items()):
            print(anon_id, timestamp)
            for root, dirs, files in os.walk(prearchive_path + timestamp):
                for file in files:
                    correct_modality = file_modality_check(file)
                    if file.endswith(".dcm") and correct_modality:
                        filepath = os.path.join(root, file)

                        now = str(datetime.datetime.now())
                        now = now.replace(":", "_")
                        now = now.replace(" ", "_")
                        new_location = f"extracted/{anon_id}_file{count}_" + str(now) + ".dcm"
                        shutil.copy(filepath, new_location)
                        anonymisation(script_path, new_location, anon_id, project_id)
            bar.next()


def file_modality_check(filepath):
    rtss_uid = "1.2.840.10008.5.1.4.1.1.481"
    file_bool = False

    try:
        dcm_dataset = pydicom.read_file(filepath)
        sop_class_uid_tag = dcm_dataset['00080016'].value
        file_bool = rtss_uid in str(sop_class_uid_tag)
    except Exception as e:
        pass

    return file_bool


def file_info(timestamps_dict):
    num_files = len(timestamps_dict)
    print("Total number of files found in prearchive: ", num_files)
    bytes_total = 0

    with open("login_details.json", 'r') as details_file:
        details = json.load(details_file)
    pre_path = details['prearchive_path']
    # pre_path = input("Absolute path to prearchive data: ")

    for folder in timestamps_dict.values():
        for root, dirs, files in os.walk(pre_path + folder):
            for file in files:
                if file.endswith(".dcm"):
                    filepath = os.path.join(root, file)
                    bytes_total += os.stat(filepath).st_size
    print(f"Total size of data found: {bytes_total/1000**3}GB")
    return pre_path, num_files


def anon_insertion(anon_name, project_id, script_path):
    # (0010,0010) DICOM tag
    new_name = f"\n(0010,0010) := \"{anon_name}\" // Anonymised Patient Name\n"
    # (0010,0020) DICOM tag
    new_id = f"\n(0010,0020) := \"{anon_name}\" // Anonymised Patient ID\n"

    # study_desc = f"\n(0008,1030) := \"{project_id}\" // Study Description\n"
    project_line = f"\nproject := \"{project_id}\"\n"
    session = "\nsession := format[\"{0}_{1}_{2}\", scanDate2, scanTime2, scannerName2]\n"
    patient_comments = f"\n(0010,4000) := format[\"Project: {project_id}; " + \
                       f"Subject: {anon_name}; " \
                       "Session: {0}; " + \
                       f"AA:True\", session] // Patient Comments\n"
    # "(0008,0020), substring[(0008,0030), 0, 6], (0008,1090) // Patient Comments"

    with open(script_path, 'r') as standard_script:
        content = standard_script.read()

    custom_script_path = "customised_script.das"
    with open(custom_script_path, 'w') as custom_script:
        custom_script.write(content)
        custom_script.write(new_name)
        custom_script.write(new_id)
        custom_script.write(project_line)
        custom_script.write(session)
        # custom_script.write(study_desc)
        custom_script.write(patient_comments)

    return custom_script_path


def anonymisation(script_path, file_path, anon_id, project_id):
    custom_script_path = anon_insertion(anon_id, project_id, script_path)

    jar_path = "dicom-edit.jar"
    run_jar = f"java -jar {jar_path}"

    command = f"{run_jar} -s {custom_script_path} -i {file_path} -o {file_path}"
    anon = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    jar_error = anon.stderr.read().decode('utf-8')

    if re.search(r"\b" + re.escape('error') + r"\b", jar_error, flags=re.IGNORECASE):
        print("Error in anonymisation;", jar_error)
        raise SystemExit


def main():
    # project = input(f"Enter Project ID: ")
    project = "RPYS_RPACS01"

    dom, u, pw = get_login_details()
    wanted_list = read_session_file()
    prearchive_dictionary = get_xnat_session_list(dom, u, pw, project)
    # print("session: timestamp", prearchive_dictionary)
    # print("session: anon_id", wanted_list)

    matched_dict = {wanted_list[k]: prearchive_dictionary[k] for it, k in
                    enumerate(prearchive_dictionary.keys() & wanted_list.keys())}

    prearchive_path, number_of_files = file_info(matched_dict)

    continue_check = input("Continue? [y/N]: ")
    if continue_check == "y":
        copy_data(prearchive_path, matched_dict, project, number_of_files)


if __name__ == "__main__":
    main()


# # can't seem to download data directly from prearchive with REST, at least for ROI Collections :(
# def get_session(domain, user, pw):
#     download = requests.get(f'{domain}/data/prearchive/projects/Unassigned/20201127_170233013',
#                             auth=(user, pw), verify=False)
#     print(download.status_code, download.text)
#
#     file_path = "test_download.zip"
#     with open(f"{file_path}", 'wb') as file:
#         file.write(download.content)


# def save_output(lines):
#     filename = asksaveasfilename(defaultextension=".txt")
#     if not filename:
#         print("File creation cancelled...")
#         raise SystemExit
#     else:
#         with open(filename, 'w', newline='') as file:
#             for item in lines:
#                 file.write("%s\n" % item)
#         print(f"File Created!\nFile is located at '{filename}'")
