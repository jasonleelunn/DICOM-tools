#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import os
from tkinter.filedialog import askdirectory

import pydicom
import requests

import keystore.keystore as keystore


def read_dicom_header(dicom_file_path):
    header = pydicom.read_file(dicom_file_path, stop_before_pixels=True)

    return header


def find_dicom_files(folder):
    file_paths = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".dcm"):
                file_paths.append(os.path.join(root, file))

    return file_paths


def get_xnat_subject_details(domain, project_id):
    request_object = xnat_session.get(f"{domain}/data/projects/{project_id}/subjects")
    request_json = request_object.json()
    subject_list_full_data = request_json['ResultSet']['Result']

    subject_identities = {}

    for subject_object in subject_list_full_data:
        subject_label = subject_object['label']
        subject_id = subject_object['ID']

        subject_identities[subject_label] = subject_id

    return subject_identities


def search_xnat_ct_sessions(domain, subject_id, rt_frame_uid):
    request_object = xnat_session.get(f"{domain}/data/subjects/{subject_id}/experiments")
    request_json = request_object.json()
    experiment_list_full_data = request_json['ResultSet']['Result']
    print(experiment_list_full_data)

    exit()


def main():
    label, url, username, password = keystore.retrieve_entry_details()
    xnat_session.auth = (username, password)

    project_id = input("Enter Project ID: ")
    subject_dict = get_xnat_subject_details(url, project_id)
    print(subject_dict)

    local_folder = askdirectory()
    dicom_files = find_dicom_files(local_folder)

    for file in dicom_files:
        local_dicom_header = read_dicom_header(file)
        patient_name = local_dicom_header['00100010'].value
        frame_of_reference_uid = local_dicom_header['30060010'][0]['00200052'].value

        print(patient_name)

        # try:
        subject_id = subject_dict[patient_name]
        print(subject_id)
        # except KeyError as e:
        #     continue
        # else:
        #     search_xnat_ct_sessions(url, subject_id, frame_of_reference_uid)


if __name__ == "__main__":
    with requests.Session() as xnat_session:
        main()
