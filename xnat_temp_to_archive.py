#!/usr/bin/env python3

"""
Script to automate downloading data files from the project resource location on XNAT, modifying their DICOM header
and then re-uploading to the archive

Author: Jason Lunn, The Institute of Cancer Research, UK
"""

import os
import shutil
import pathlib
import time

import pydicom
import requests
import tempfile
import zipfile

import keystore.keystore as keystore

CWD = os.path.dirname(os.path.realpath(__file__))


class App:
    def __init__(self, session, domain, project_id):
        self.session = session
        self.domain = domain
        self.project_id = project_id

        self.next_to_do = ["OCTA_C_GU_116"]
        self.zip_files_not_processed = []

        self.download_from_temp()

        print(self.zip_files_not_processed)

    def download_from_temp(self):
        file_list_request = self.session.get(f"{self.domain}/data/projects/{self.project_id}/"
                                             f"resources/temporary/files?format=json")

        for file_info in file_list_request.json()['ResultSet']['Result']:
            if ".zip" in file_info['Name']:
                if len(file_info['Name']) == 17:
                    anon_id = file_info['Name'][:13]
                    print(anon_id)

                    if self.next_to_do:
                        if anon_id in self.next_to_do:
                            self.next_to_do = []
                        else:
                            continue

                    self.file_download_request = self.session.get(f"{self.domain}{file_info['URI']}")

                    global CWD
                    temp_dir = pathlib.Path(f"{CWD}/temp/")
                    with tempfile.TemporaryDirectory(dir=temp_dir, prefix="temp_to_archive_") as dir_path:
                        self.download_path = pathlib.Path(f"{dir_path}/downloaded")
                        self.raw_path = pathlib.Path(f"{dir_path}/raw_data")
                        self.upload_path = pathlib.Path(f"{dir_path}/upload")

                        self.unzip_data()

                        try:
                            self.modify_dicom_header(anon_id)
                        except AttributeError as e:
                            self.zip_files_not_processed.append(file_info['Name'])
                            continue

                        self.zip_data()
                        self.upload_data()

                else:
                    self.zip_files_not_processed.append(file_info['Name'])

    def unzip_data(self):
        with open(f"{self.download_path}", 'wb') as file:
            file.write(self.file_download_request.content)
        with zipfile.ZipFile(self.download_path, 'r') as zip_ref:
            zip_ref.extractall(self.raw_path)

    def modify_dicom_header(self, anon_id):
        anon_num_only = ''.join(filter(str.isdigit, anon_id))
        dicom_path = pathlib.Path(f"{self.raw_path}")
        for file_path in walk_directory(dicom_path):
            if file_path.is_file():
                header = pydicom.read_file(file_path, force=True)

                header.PatientName = anon_id
                header.PatientID = anon_id

                session_date = header.StudyDate
                session_time = header.StudyTime
                session_label = f"{session_date}_{session_time}_{anon_num_only}_POST"

                header.PatientComments = f"Project: {self.project_id}; Subject: {anon_id}; " \
                                         f"Session: {session_label}; AA:true"

                header.save_as(file_path)

    def zip_data(self):
        shutil.make_archive(str(self.upload_path), 'zip', str(self.raw_path))

    def upload_data(self):
        scan_upload_request = self.session.post(
            f'{self.domain}/data/services/import?inbody=true&import-handler=DICOM-zip'
            f'&dest=/archive', data=open(f"{self.upload_path}.zip", 'rb'))
        print(scan_upload_request.status_code)


def walk_directory(start_path):
    # retrieve all files recursively in directory
    for path in pathlib.Path(start_path).iterdir():
        if path.is_dir():
            yield from walk_directory(path)
            continue
        yield path.resolve()


def main():
    # get XNAT details
    xnat_label, url, username, password = keystore.retrieve_entry_details(selected_id=6)

    project_id = "OCTAPUS_GSTT"

    with requests.Session() as xnat_session:
        xnat_session.auth = (username, password)
        App(xnat_session, url, project_id)


if __name__ == "__main__":
    main()
