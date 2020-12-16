#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

# Script to automate using the CLI etherj tool 'rtsedit' on multiple RTSTRUCT files to edit ROI collections

import re
import csv
import json
import os
import subprocess
import datetime
import pydicom
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


def get_roi_labels(filename):
    file = pydicom.read_file(filename, force=True)
    labels = []
    file_type_check = False
    if 'RTSTRUCT' in file.Modality:
        file_type_check = True
        sequences = file.StructureSetROISequence

        for sequence in sequences:
            label = sequence.ROIName
            labels.append(label)
    else:
        msg = "The file object is not recognised as being RTS"
        # raise Exception(msg)

    return labels, file_type_check


def compare_labels(requested_labels, all_labels, patient_id):
    print(f"ALL LABELS for {patient_id}: ", all_labels)
    print(f"WANTED LABELS for {patient_id}: ", requested_labels)

    all_check = all(elem in all_labels for elem in requested_labels)

    if all_check:
        print("All requested ROIs present")
    else:
        missing = list(set(requested_labels).difference(all_labels))
        print(f"MISSING LABELS for {patient_id}: ", missing)


def rtsedit(input_data, wrong_list):
    clean_edit = False
    roi_info = "BLANK"

    anon_id = input_data[0]
    include_rois = input_data[1:]

    edit_path = "etherj-cli-tools/bin/rtsedit"

    files = find_file(anon_id)

    for file in files:

        found_labels, file_type_bool = get_roi_labels(file)

        if file_type_bool:
            compare_labels(include_rois, found_labels, anon_id)
            continue
            now = str(datetime.datetime.now())
            now = now.replace(":", "_")
            now = now.replace(" ", "_")

            output_file_name = "MOD_" + anon_id + "_" + now + ".dcm"
            output_file = "modified/" + output_file_name

            joint = '\" \"'
            rois = re.split('(?<![a-zA-Z0-9-%]) ', f"\"{joint.join(include_rois)}\"")

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
            elif edit_output and output_bool:
                roi_info = edit_output
                move_file(output_file, output_file_name)

    if not clean_edit:
        wrong_list[anon_id] = roi_info


def move_file(filepath, filename):
    move_cmd = f"mv {filepath} modified/bad_edit/{filename}"
    move = subprocess.Popen(move_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def save_summary(problems_dict):
    now = str(datetime.datetime.now())
    now = now.replace(":", "_")
    now = now.replace(" ", "_")

    with open(f"modified/error_logs/{now}_batch_rtsedit_errors.txt", 'w', newline='\r\n') as f:
        # print(problems_dict)
        json.dump(problems_dict, f, sort_keys=True, indent=0)


def main():
    data_list = read_input_file()
    count = 0
    wrong_list = {}

    for data in data_list:
        count += 1
        print(f"\nEditing RTSTRUCT for patient {data[0]} ({count}/{len(data_list)})")
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
