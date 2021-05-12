#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import re
import os
import subprocess
from tkinter.filedialog import askopenfilename


def find_files():
    filepaths = []
    for root, dirs, files in os.walk(rtss_folder):
        for file in files:
            if file.endswith(".dcm"):
                filepaths.append(os.path.join(root, file))

    print("Number of files found: ", len(filepaths))
    return filepaths


def anon_insertion(anon_name, script_path):
    # (0010,0010) DICOM tag
    new_name = f"\n(0010,0010) := \"{anon_name}\" // Anonymised Patient Name\n"
    # (0010,0020) DICOM tag
    new_id = f"\n(0010,0020) := \"{anon_name}\" // Anonymised Patient ID\n"

    # study_desc = f"\n(0008,1030) := \"{project_id}\" // Study Description\n"
    # project_line = f"\nproject := \"{project_id}\"\n"
    # session = "\nsession := format[\"{0}_{1}{2}\", scanDate2, scanTime2, scannerName2]\n"
    # patient_comments = f"\n(0010,4000) := format[\"Project: {project_id}; " + \
    #                    f"Subject: {anon_name}; " \
    #                    "Session: {0}; " + \
    #                    f"AA:True\", session] // Patient Comments\n"
    # "(0008,0020), substring[(0008,0030), 0, 6], (0008,1090) // Patient Comments"

    with open(script_path, 'r') as standard_script:
        content = standard_script.read()

    custom_script_path = "customised_script.das"
    with open(custom_script_path, 'w') as custom_script:
        custom_script.write(content)
        custom_script.write(new_name)
        custom_script.write(new_id)
        # custom_script.write(project_line)
        # custom_script.write(session)
        # # custom_script.write(study_desc)
        # custom_script.write(patient_comments)

    return custom_script_path


def anonymisation(script_path, file_path, anon_id):
    custom_script_path = anon_insertion(anon_id, script_path)

    jar_path = "dicom-edit.jar"
    run_jar = f"java -jar {jar_path}"

    print(f"modified/fixed/{file_path[len(rtss_folder):]}")

    command = f"{run_jar} -s {custom_script_path} -i {file_path} -o modified/fixed/{file_path[len(rtss_folder):]}"
    anon = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    jar_error = anon.stderr.read().decode('utf-8')

    if re.search(r"\b" + re.escape('error') + r"\b", jar_error, flags=re.IGNORECASE):
        print("Error in anonymisation;", jar_error)
        raise SystemExit


def main():
    filepaths = find_files()
    script_path = askopenfilename(title="Choose an anonymisation profile")
    example_id = input("Enter example anon ID: ")

    for file in filepaths:
        anon_id = file[len(rtss_folder):len(rtss_folder)+len(example_id)]
        print("Processing: ", anon_id)
        anonymisation(script_path, file, anon_id)


if __name__ == "__main__":
    rtss_folder = input("Path to files: ")
    main()
