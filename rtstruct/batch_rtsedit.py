#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

# Script to automate using the CLI etherj tool 'rtsedit' on multiple RTSTRUCT files to edit ROI collections
import pathlib
import re
import csv
import json
import os
import subprocess
import datetime
import pydicom
import argparse
from tkinter.filedialog import askopenfilename, askdirectory
from difflib import get_close_matches


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


def find_all_files():
    filepaths = []
    for root, dirs, files in os.walk(rtss_folder):
        for file in files:
            if file.endswith(".dcm"):
                filepaths.append(os.path.join(root, file))

    return filepaths


def read_dicom_file(file):
    header = pydicom.read_file(file, force=True, stop_before_pixels=True)

    return header


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


def empty_roi_check(filename):
    file = pydicom.read_file(filename, force=True)

    empty_roi_list = []
    roi_dict = {}

    if 'RTSTRUCT' in file.Modality:

        info_sequence = file.StructureSetROISequence
        for seq in info_sequence:
            roi_dict[seq.ROINumber] = seq.ROIName

        contour_sequence = file.ROIContourSequence
        for seq in contour_sequence:
            try:
                contour_metadata = seq.ContourSequence
            except AttributeError as e:
                # print(e)
                roi_number_contour = seq.ReferencedROINumber
                roi_name = roi_dict[roi_number_contour]
                empty_roi_list.append(roi_name)

    return empty_roi_list


def compare_labels(requested_labels, all_labels, patient_id):

    missing = []
    all_check = all(elem in all_labels for elem in requested_labels)

    if not all_check:
        missing = list(set(requested_labels).difference(all_labels))
        # print(f"MISSING LABELS for {patient_id}: ", missing)

    return missing


def label_conversion(missing_list, full_list, changes, anon_id):
    matches = []
    for missing in missing_list:
        match = get_close_matches(missing, full_list, n=3, cutoff=0.75)
        # print(f"MATCHES FOUND for {missing}: ", match)
        if match:

            digits_only_missing = ''.join(filter(str.isdigit, missing))
            if digits_only_missing != "":
                for i in range(len(match)):
                    digits_only_match = ''.join(filter(str.isdigit, match[i]))

                    if digits_only_missing == digits_only_match:
                        matches.append(match[i])
                        alter_string = f" \'{missing}\' ==> \'{match[i]}\' ({i+1}/{len(match)})"
                        changes.append((anon_id, alter_string))
                        break
                    else:
                        alter_string = f" \'{missing}\' IS NOT \'{match[i]}\' ({i+1}/{len(match)})"
                        changes.append((anon_id, alter_string))

            else:
                matches.append(match[0])
                alter_string = f" \'{missing}\' ==> \'{match[0]}\'"
                changes.append((anon_id, alter_string))
        else:
            matches.append(missing)
            no_string = f"Couldn't find replacement for \'{missing}\'"
            changes.append((anon_id, no_string))

    return matches


def rtsedit(anon_id, input_data, files, wrong_list, changes_list, empty_list):
    clean_edit = False
    roi_info = "BLANK"

    edit_path = "../etherj-cli-tools/bin/rtsedit"

    # add feature to look in all relevant files and split ROIs correctly
    for file in files:
        include_rois = input_data
        found_labels, file_type_bool = get_roi_labels(file)
        empty_labels = empty_roi_check(file)

        if args.strings:
            include_rois = []
            for roi_string in input_data:
                # print("found: ", found_labels)
                # print(roi_string, include_rois)
                # requested_ctv_check = [roi for roi in include_rois if re.search(re.escape('ctv'), roi, flags=re.IGNORECASE)]
                present_string_check = [roi for roi in found_labels if
                                        re.search(re.escape(roi_string), roi, flags=re.IGNORECASE)]

                if present_string_check:
                    include_rois.extend(present_string_check)

        if file_type_bool:

            # if empty_labels:
            #     found_labels = [e for e in found_labels if e not in empty_labels]
            #     empty_list[anon_id] = empty_labels

            missing_labels = compare_labels(include_rois, found_labels, anon_id)

            if missing_labels:
                include_rois = [e for e in include_rois if e not in missing_labels]

                converted_labels = label_conversion(missing_labels, found_labels, changes_list, anon_id)
                include_rois += converted_labels
                # print(f"UPDATED LABELS for {anon_id}: ", include_rois)

            if empty_labels:
                include_rois = [e for e in include_rois if e not in empty_labels]
                empty_list[anon_id] = empty_labels


            # continue
            now = str(datetime.datetime.now())
            now = now.replace(":", "_")
            now = now.replace(" ", "_")

            output_file_name = "ALT_" + anon_id + "_" + now + ".dcm"
            output_file = "modified/" + output_file_name

            joint = '\" \"'
            rois = re.split('(?<![a-zA-Z0-9-%]) ', f"\"{joint.join(include_rois)}\"")

            # command = f"{edit_path} --label MOD_+ --include \"{joint.join(include_rois)}\" --output {output_file} {file}"
            command_list = [edit_path, "--label", "ALT_RTSS", "--include", *rois, "--output", output_file, file]

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

            no_changes_bool = re.search(r"\b" + re.escape('No ROIs would be removed')
                                        + r"\b", edit_output, flags=re.IGNORECASE)

            if no_changes_bool and args.changes:
                print("Copying file...")
                global copy_count
                copy_count += 1
                copy_file(file, output_file)
            label_edit(output_file)

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


def copy_file(filepath, filename):
    copy_cmd = f"cp {filepath} {filename}"
    copy = subprocess.Popen(copy_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def dot_das_insertion():
    now = str(datetime.datetime.now())
    date = now[:10].replace("-", "")
    time = now[11:19].replace(":", "")

    series_date = f"\n(0008,0021) := \"{date}\" // Series Date\n"
    series_time = f"\n(0008,0031) := \"{time}\" // Series Time\n"

    with open(script_path, 'r') as standard_script:
        content = standard_script.read()

    custom_script_path = "customised_script.das"
    with open(custom_script_path, 'w') as custom_script:
        custom_script.write(content)
        # custom_script.write(series_date)
        # custom_script.write(series_time)

    return custom_script_path


def label_edit(file_path):
    # custom_script_path = dot_das_insertion()
    custom_script_path = script_path
    jar_path = "../dicom-edit.jar"
    run_jar = f"java -jar {jar_path}"

    command = f"{run_jar} -s {custom_script_path} -i {file_path} -o {file_path}"
    anon = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    jar_error = anon.stderr.read().decode('utf-8')

    if re.search(r"\b" + re.escape('error') + r"\b", jar_error, flags=re.IGNORECASE):
        print("Error in anonymisation;", jar_error)
        raise SystemExit


def save_summary(problems_dict, changes_list, empty_dict):
    now = str(datetime.datetime.now())
    now = now.replace(":", "_")
    now = now.replace(" ", "_")

    with open(f"modified/error_logs/{now}_batch_rtsedit_errors.txt", 'w', newline='\r\n') as f:
        # print(problems_dict)
        json.dump(problems_dict, f, sort_keys=True, indent=0)

    with open(f"modified/error_logs/{now}_batch_rtsedit_changes.csv", 'w', newline='') as file:
        write = csv.writer(file, delimiter=',')
        write.writerows(changes_list)

    with open(f"modified/error_logs/{now}_batch_rtsedit_empty_rois.txt", 'w', newline='') as f:
        json.dump(empty_dict, f, sort_keys=True, indent=0)


def cli_args():
    parser = argparse.ArgumentParser(
        description="A program to automate the editing of ROI's in DICOM Radiotherapy Structure files.")

    parser.add_argument("-s", "--strings",
                        help="enable named string ROI addition", default=False, action='store_true')

    parser.add_argument("-n", "--changes",
                        help="enable copying unchanged files", default=False, action='store_true')

    args_int = parser.parse_args()
    return args_int


def main():
    roi_strings = []
    wrong_list = {}
    changes_list = []
    empty_list = {}

    if args.strings:
        print("Enter strings for search, enter \"DONE\" to move on.")
        while True:
            roi_string_input = input("Enter string to search for in ROI labels: ")
            roi_strings.append(roi_string_input)

            if roi_string_input == "DONE":
                roi_strings.pop(-1)
                break
        print("Strings to search for: ", roi_strings)

        files = find_all_files()
        for count, file in enumerate(files):
            dicom_header = read_dicom_file(file)
            anon_id = str(dicom_header['00100010'].value)
            num_of_files = len(files)
            print(f"\nEditing RTSTRUCT for subject {anon_id} ({count+1}/{num_of_files})")
            rtsedit(anon_id, roi_strings, [file], wrong_list, changes_list, empty_list)

    else:
        data_list = read_input_file()
        count = 0

        for data in data_list:
            count += 1
            anon_id = data[0]
            files = find_file(anon_id)
            print(f"\nEditing RTSTRUCT for patient {anon_id} ({count}/{len(data_list)})")
            rtsedit(anon_id, data[1:], files, wrong_list, changes_list, empty_list)

    if wrong_list:
        print(f"Patients for which files were not edited correctly;")
        print(*wrong_list.keys(), sep='\n')
        # print(f"Number of patients with files not edited correctly = {len(wrong_list)}/{len(data_list)}")

    save_summary(wrong_list, changes_list, empty_list)

    if copy_count != 0:
        print(f"Number of copied unedited files: {copy_count}")

    print("\nBatch rtsedit Complete!")


if __name__ == "__main__":
    args = cli_args()
    rtss_folder = pathlib.Path(askdirectory())
    script_path = "rtssLabelEdit.das"
    copy_count = 0
    main()
