#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import re
import csv
import subprocess
import requests
import datetime
from tkinter.filedialog import askopenfilename


def get_login_details():
    domain = input(f"Enter XNAT Domain: ")
    username = input(f"Enter Username for {domain}: ")
    password = input(f"Enter Password for {username}@{domain}: ")

    return domain, username, password


def read_input_file():
    filename = askopenfilename(title="Select an Input File")
    with open(filename, 'r') as file:
        wanted_list = list(csv.reader(file, delimiter=','))
        # wanted_list = [line.rstrip() for line in file]
    return wanted_list


def anon_insertion(anon_name, project_id, script_path):
    # (0010,0010) DICOM tag
    new_name = f"\n(0010,0010) := \"{anon_name}\" // Anonymised Patient Name\n"
    # (0010,0020) DICOM tag
    # new_id = f"\n(0010,0020) := \"{anon_id}\" // Anonymised Patient ID\n"

    # study_desc = f"\n(0008,1030) := \"{project_id}\" // Study Description\n"
    project_line = f"\nproject := \"{project_id}\"\n"
    session = "\nsession := format[\"{0}_{1}{2}\", scanDate2, scanTime2, scannerName2]\n"
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
        # custom_script.write(new_id)
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


def extraction(domain, user, pw, project, input_list):
    extraction_path = "extracted/"
    script_path = askopenfilename(title="Choose an anonymisation profile")

    found_counter = 0
    not_found_list = []

    for patient in range(len(input_list)):

        name = input_list[patient][0]
        experiment = input_list[patient][1][:15]
        anon_id = input_list[patient][2]

        try:
            experiments_request = requests.get(f'{domain}/data/projects/{project}/subjects/{name}'
                                               f'/experiments', auth=(user, pw), verify=False)
            experiment_json = experiments_request.json()
            experiment_list = []
            [experiment_list.append(exp['label']) for exp in experiment_json['ResultSet']['Result']]

            match_exp = [f for f in experiment_list if experiment in f]

            if match_exp:
                scans_request = requests.get(f'{domain}/data/projects/{project}/subjects/{name}'
                                             f'/experiments/{match_exp[0]}/scans', auth=(user, pw), verify=False)
                scan_json = scans_request.json()
                scan_list = []
                [scan_list.append(scan['ID']) for scan in scan_json['ResultSet']['Result']]

                for scan in scan_list:
                    files_request = requests.get(f'{domain}/data/projects/{project}/subjects/{name}'
                                                 f'/experiments/{experiment}/scans/{scan}/files', auth=(user, pw), verify=False)
                    file_json = files_request.json()
                    file_list = []
                    [file_list.append(file['Name']) for file in file_json['ResultSet']['Result']]

                    matching = [f for f in file_list if "RTSTRUCT" in f]

                    for file in matching:
                        file_download = requests.get(f'{domain}/data/projects/{project}/subjects/{name}'
                                                     f'/experiments/{experiment}/scans/{scan}/files/{file}',
                                                     auth=(user, pw), verify=False)

                        now = str(datetime.datetime.now())[:19]
                        now = now.replace(":", "_")
                        now = now.replace(" ", "_")

                        file_path = extraction_path + anon_id + "_" + now + ".dcm"

                        with open(file_path, 'wb') as save_file:
                            save_file.write(file_download.content)
                        anonymisation(script_path, file_path, anon_id, project)

                        found_counter += 1

                        break
            else:
                print(f"Patient {name} found, but session {experiment} not found")
        except:
            not_found_list.append(name)

    return found_counter, not_found_list


def main():
    project = input(f"Enter Project ID: ")
    # project = "TEST_UPLOAD"
    dom, u, pw = get_login_details()
    wanted_list = read_input_file()
    found_count, non_list = extraction(dom, u, pw, project, wanted_list)

    print(f"Found {found_count} RTSTRUCT files for {len(wanted_list)} patients")

    if non_list:
        print(f"Patients not found;")
        print(*non_list, sep='\n')


if __name__ == "__main__":
    main()
