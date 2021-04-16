#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import json
import pydicom
import getpass
from tkinter import filedialog
from pathlib import Path
import requests
import shutil
import os
import tempfile
from progress.bar import Bar


class FancyBar(Bar):
    # message = 'Loading'
    # fill = '*'
    suffix = '%(percent).2f%% - %(eta)ds'


def get_xnat_details():

    with open("login_details.json", 'r') as details_file:
        details = json.load(details_file)
    domain = details['domain']
    username = details['username']
    password = getpass.getpass(prompt=f"Enter Password for {username}@{domain}: ")
    # password = details['password']
    project_id = details['project_id']

    return domain, username, password, project_id


def select_data_folder():
    # causes MacOS to crash and log user out, need to find alternative
    directory = Path(filedialog.askdirectory())

    return directory


def append_patient_comments_tag(directory, project_id):
    # spinner = Spinner('Preparing data for XNAT upload... ')
    files = Path(directory).rglob('*.dcm')
    for file in files:
        dcm_dataset = pydicom.read_file(file)
        subject_name = dcm_dataset['00100010'].value
        scan_date = dcm_dataset['00080020'].value
        scan_time = dcm_dataset['00080030'].value
        full_scanner_name = dcm_dataset['00081090'].value
        # scanner_name = full_scanner_name.split()[0]

        session_label = f"{scan_date}_{scan_time}_{full_scanner_name}"

        patient_comments = f"Project: {project_id}; Subject: {subject_name}; Session: {session_label}; AA:True"
        dcm_dataset['00104000'].value = patient_comments
        dcm_dataset.save_as(file)

        # spinner.next()


def send_to_xnat(xnat_session, domain, directory, project_id):

    files = Path(directory).rglob('*.dcm')
    files_list = list(files)
    total_files = len(files_list)
    with tempfile.TemporaryDirectory(dir=Path("temp/")) as temp_area:
        file_area = Path(f"{temp_area}/file_area")
        make_file_dir(file_area)
        print("\n")
        with FancyBar('Uploading data to XNAT... ', max=total_files) as bar:
            for i, file in enumerate(files_list):
                temp_file = Path(f"{temp_area}/file_area/{file.stem}{file.suffix}")
                shutil.copyfile(file, temp_file)

                # send DICOM files in batches to prevent spamming requests to the server
                if i % 200 == 0 or i % (total_files - 1) == 0:
                    append_patient_comments_tag(file_area, project_id)
                    zip_temp_area = Path(f"{temp_area}/zipped_up")
                    shutil.make_archive(zip_temp_area, 'zip', file_area)

                    with open(f"{zip_temp_area}.zip", 'rb') as data:
                        file_upload_request = xnat_session.post(f'{domain}/data/services/import'
                                                                f'?inbody=true&import-handler=DICOM-zip'
                                                                f'&dest=/archive', data=data)

                    clean_temp_dir(temp_area)
                    make_file_dir(file_area)

                bar.next()


def make_file_dir(location):
    Path(location).mkdir(parents=True, exist_ok=True)


def clean_temp_dir(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def main():
    # clean_temp_dir("temp")
    domain, username, password, project_id = get_xnat_details()
    data_directory = select_data_folder()
    # append_patient_comments_tag(data_directory, project_id)
    with requests.Session() as xnat_session:
        xnat_session.auth = (username, password)
        send_to_xnat(xnat_session, domain, data_directory, project_id)

    print("\nUpload Complete!")


if __name__ == "__main__":
    main()
