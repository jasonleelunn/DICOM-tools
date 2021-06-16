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


def search_xnat_sessions(domain, project_id, subject_id):
    request_object = xnat_session.get(f"{domain}/data/projects/{project_id}/subjects/{subject_id}/experiments?format"
                                      f"=json")
    request_json = request_object.json()
    sessions_list_full_data = request_json['ResultSet']['Result']

    return sessions_list_full_data


def search_xnat_scans(domain, session_id):
    request_object = xnat_session.get(f"{domain}/data/experiments/{session_id}/scans?format=json")
    request_json = request_object.json()
    scans_list_full_data = request_json['ResultSet']['Result']

    return scans_list_full_data


def download_xnat_scan_header(domain, project_id, subject_id, session_id, scan_id):
    request_object = xnat_session.get(f"{domain}/data/services/dicomdump?src=/archive/projects/{project_id}/"
                                      f"subjects/{subject_id}/experiments/{session_id}/scans/{scan_id}")
    request_json = request_object.json()
    scan_header = request_json['ResultSet']['Result']

    return scan_header


def get_tag_data_from_xnat_header(xnat_scan_header, tag_number: str):
    found_tag_dict = list(filter(lambda tag_dict: tag_dict['tag1'] == tag_number, xnat_scan_header))[0]

    return found_tag_dict


def modify_local_file_uids(xnat_scan_header, local_file_header, local_file_path):
    study_uid_tag_dict = get_tag_data_from_xnat_header(xnat_scan_header, '(0020,000D)')
    series_uid_tag_dict = get_tag_data_from_xnat_header(xnat_scan_header, '(0020,000E)')

    study_uid = study_uid_tag_dict['value']
    series_uid = series_uid_tag_dict['value']

    local_file_header['30060010'][0]['30060012'][0]['00081155'].value = study_uid
    local_file_header['30060010'][0]['30060012'][0]['30060014'][0]['0020000e'].value = series_uid

    local_file_header.save_as(local_file_path)


def main():
    label, url, username, password = keystore.retrieve_entry_details()
    xnat_session.auth = (username, password)

    project_id = input("Enter Project ID: ")
    subject_dict = get_xnat_subject_details(url, project_id)

    local_folder = askdirectory()
    dicom_files = find_dicom_files(local_folder)

    for file in dicom_files:
        local_dicom_header = read_dicom_header(file)
        patient_name = str(local_dicom_header['00100010'].value)
        frame_of_reference_uid = local_dicom_header['30060010'][0]['00200052'].value

        try:
            subject_id = subject_dict[patient_name]
        except KeyError as e:
            continue
        else:
            list_of_sessions = search_xnat_sessions(url, project_id, subject_id)
            for session in list_of_sessions:
                session_id = session['ID']
                list_of_scans = search_xnat_scans(url, session_id)
                for scan in list_of_scans:
                    scan_id = scan['ID']
                    xnat_scan_header = download_xnat_scan_header(url, project_id, subject_id, session_id, scan_id)
                    modality_tag_dict = get_tag_data_from_xnat_header(xnat_scan_header, '(0008,0060)')

                    if modality_tag_dict['value'] == 'CT':
                        frame_uid_tag_dict = get_tag_data_from_xnat_header(xnat_scan_header, '(0020,0052)')

                        if frame_uid_tag_dict['value'] == frame_of_reference_uid:
                            modify_local_file_uids(xnat_scan_header, local_dicom_header, file)

                    else:
                        continue


if __name__ == "__main__":
    with requests.Session() as xnat_session:
        main()
