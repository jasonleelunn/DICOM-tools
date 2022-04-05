#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

"""
Script to check all data in an XNAT project and generate JSON report on which sessions contain DICOM data with any
private tags
"""

import json
import pathlib
import time
import requests

from keystore import keystore


class PrivateTagCheck:
    def __init__(self, xnat_label, xnat_session, xnat_domain, project_id):
        self.xnat_label = xnat_label
        self.xnat_session = xnat_session
        self.domain = xnat_domain
        self.project_id = project_id

        self.report_dict = {project_id: {}}

    def xnat_json_request(self, uri):
        try:
            request_object = self.xnat_session.get(f"{self.domain}/data/{uri}")
        except requests.ConnectionError as e:
            # print("Rate limited, retrying request...")
            time.sleep(2)
            results_list = self.xnat_json_request(uri)
        else:
            try:
                request_json = request_object.json()
            except json.JSONDecodeError as json_error:
                results_list = None
            else:
                results_list = request_json['ResultSet']['Result']

        return results_list

    def search_project(self):

        subject_list = self.xnat_json_request(f"projects/{self.project_id}/subjects?format=json")

        for subject in subject_list:
            subject_label = subject['label']
            session_list = self.xnat_json_request(f"projects/{self.project_id}/subjects/{subject_label}/"
                                                f"experiments?format=json")
            if session_list:
                for session in session_list:
                    session_label = session['label']
                    scan_list = self.xnat_json_request(f"projects/{self.project_id}/subjects/{subject_label}/"
                                                        f"experiments/{session_label}/scans?format=json")
                    for scan in scan_list:
                        scan_id = scan['ID']
                        dicom_header = self.xnat_json_request(f"services/dicomdump?src=/archive/projects/{self.project_id}/"
                                                              f"subjects/{subject_label}/experiments/{session_label}/scans/{scan_id}"
                                                              f"&format=json")
                        has_private = self.private_tag_check(dicom_header)

                        if has_private:
                            self.report_dict[self.project_id] = {f"{subject_label}": {f"{session_label}": {f"{scan_id}": True}}}

        self.write_json_report()
    
    def private_tag_check(self, dicom_header):
        for tag in dicom_header:
            group_number = int(tag['tag1'][1:5])
            # check if group number is odd, indicates tag is not part of DICOM Standard i.e. it is a private tag
            if group_number % 2 != 0:
                return True
    
    def write_json_report(self):
        with open(pathlib.Path(f'./logs/{self.project_id}_private_tag_report.json'), 'w') as file:
            json.dump(self.report_dict, file, indent=4)


def main():
    xnat_label, url, username, password = keystore.retrieve_entry_details()

    project_id = input("Project ID: ")

    with requests.Session() as session:
        session.auth = (username, password)
        instance = PrivateTagCheck(xnat_label=xnat_label, xnat_session=session, xnat_domain=url, project_id=project_id)
        instance.search_project()


if __name__ == "__main__":
    main()
