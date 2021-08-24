#!/usr/bin/env python3

"""
Script to add Study ID Attribute (0020, 0010) to the metadata of DICOM files using the local directory structure
names to differentiate studies of different time series

Author: Jason Lunn, The Institute of Cancer Research, UK
"""

import os

import pydicom


def find_dicom_files(folder):
    file_information = {}
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".dcm"):
                parent_dir = root.split("/")[-1]
                file_information[os.path.join(root, file)] = parent_dir

    return file_information


def modify_dicom_headers(file_info_dict):
    for file_path, parent_dir in file_info_dict.items():
        study_number = int(''.join(filter(str.isdigit, parent_dir)))

        header = pydicom.read_file(file_path, force=True)

        patient_name = header['00100010'].value

        study_id = f"{patient_name}_STUDY_{study_number:02}"
        header.StudyID = study_id

        header.PatientComments = f"Project: LIBRA_BROMPTON; Subject: {patient_name}; Session: {study_id}; AA:true"

        header.save_as(file_path)


def main():
    input_directory = ""

    file_info_dict = find_dicom_files(input_directory)
    modify_dicom_headers(file_info_dict)


if __name__ == "__main__":
    main()
