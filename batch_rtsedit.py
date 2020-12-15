#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

# Script to automate using the CLI etherj tool 'rtsedit' on multiple RTSTRUCT files to edit ROI collections

import re
import csv
import json
import os
import subprocess
import datetime
from tkinter.filedialog import askopenfilename


def read_input_file():
    filename = askopenfilename(title="Select an Input File")
    # filename = "batch_test.csv"
    with open(filename, 'r') as file:
        wanted_list = list(csv.reader(file, delimiter=',', skipinitialspace=True))
    return wanted_list


def find_file(anon_id):
    filepaths = []
    for root, dirs, files in os.walk(rtss_folder):
        for file in files:
            if file.endswith(".dcm") and anon_id in file:
                filepaths.append(os.path.join(root, file))

    return filepaths


def rtsedit(input_data, wrong_list):
    clean_edit = False

    anon_id = input_data[0]
    include_rois = input_data[1:]

    edit_path = "etherj-cli-tools/bin/rtsedit"

    files = find_file(anon_id)
    # file = "rtss_test/DICOM/anon_rtss.dcm"

    for file in files:

        now = str(datetime.datetime.now())
        now = now.replace(":", "_")
        now = now.replace(" ", "_")

        output_file_name = "MOD_" + anon_id + "_" + now + ".dcm"
        output_file = "modified/" + output_file_name

        joint = '\" \"'
        rois = re.split('(?<![a-zA-Z0-9]) ', f"\"{joint.join(include_rois)}\"")

        # command = f"{edit_path} --label MOD_+ --include \"{joint.join(include_rois)}\" --output {output_file} {file}"
        command_list = [edit_path, "--label", "MOD_+", "--include", *rois, "--output", output_file, file]

        edit = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        edit_error = edit.stderr.read().decode('utf-8')
        # if re.search(r"\b" + re.escape('exception') + r"\b", edit_error, flags=re.IGNORECASE):
        #     print("Error in rtsedit process;\n\n", edit_error)
        #     wrong_list.append([anon_id, "ERROR"])
            # raise SystemExit
        error_bool = re.search(r"\b" + re.escape('exception') + r"\b", edit_error, flags=re.IGNORECASE)
        edit_output = edit.stdout.read().decode('utf-8')
        print(edit_output)
        output_bool = re.search(r"\b" + re.escape('not found') + r"\b", edit_output, flags=re.IGNORECASE)

        if not error_bool and not output_bool:
            clean_edit = True
            break
        elif edit_output:
            roi_info = edit_output

    if not clean_edit:
        wrong_list[anon_id] = roi_info


def save_summary(problems_dict):
    now = str(datetime.datetime.now())
    now = now.replace(":", "_")
    now = now.replace(" ", "_")

    with open(f"modified/error_logs/{now}_batch_rtsedit_errors.txt", 'w', newline='\r\n') as f:
        print(problems_dict)
        json.dump(problems_dict, f, sort_keys=True, indent=0)


def main():
    data_list = read_input_file()
    count = 0
    wrong_list = {}

    for data in data_list:
        count += 1
        print(f"Editing RTSTRUCT for patient {data[0]} ({count}/{len(data_list)})")
        rtsedit(data, wrong_list)

    if wrong_list:
        print(f"Patients for which files were not edited correctly;")
        print(*wrong_list.keys(), sep='\n')
        print(f"Number of patients with files not edited correctly = {len(wrong_list)}/{len(data_list)}")
        save_summary(wrong_list)

    print("\nBatch rtsedit Complete!")


if __name__ == "__main__":
    rtss_folder = input("Path to files: ")
    # rtss_folder = "rtss_test"
    main()
