#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import csv
import datetime
import json
import time

import requests

import keystore.keystore as keystore


class NameDiff:
    def __init__(self, xnat_name, xnat_domain):
        self.xnat_name = xnat_name
        self.domain = xnat_domain

        self.log_list = []

    def xnat_data_request(self, uri):
        try:
            request_object = xnat_session.get(f"{self.domain}/data/{uri}")
        except requests.ConnectionError as e:
            # print("Rate limited, retrying request...")
            time.sleep(2)
            results_list = self.xnat_data_request(uri)
        else:
            try:
                request_json = request_object.json()
            except json.JSONDecodeError as json_error:
                results_list = None
            else:
                results_list = request_json['ResultSet']['Result']

        return results_list

    def search_database(self):
        project_list = self.xnat_data_request("projects?format=json")

        for project in project_list:
            project_id = project['ID']
            subject_list = self.xnat_data_request(f"projects/{project_id}/subjects?format=json")

            for subject in subject_list:
                subject_label = subject['label']
                session_list = self.xnat_data_request(f"projects/{project_id}/subjects/{subject_label}/"
                                                      f"experiments?format=json")
                if session_list:
                    for session in session_list:
                        session_label = session['label']
                        dicom_header = self.xnat_data_request(f"services/dicomdump?src=/archive/projects/{project_id}/"
                                                              f"subjects/{subject_label}/experiments/{session_label}"
                                                              f"&format=json")
                        if dicom_header:
                            dicom_patient_name = get_tag_data_from_xnat_header(dicom_header, "(0010,0010)")
                            dicom_patient_id = get_tag_data_from_xnat_header(dicom_header, "(0010,0020)")
                            break
                        else:
                            dicom_patient_name = dicom_patient_id = "NO DATA"

                    if str(subject_label) != str(dicom_patient_name) and str(subject_label) != str(dicom_patient_id):
                        self.log_list.append([project_id, subject_label, dicom_patient_name, dicom_patient_id])

        if self.log_list:
            date, time_slice = get_date_time()
            self.write_log(date, time_slice)

    def write_log(self, date, time_slice):
        filename = f"{date}_{time_slice}_{self.xnat_name}_subject_name_diff.csv"
        header = ["Project ID", "XNAT Name", "DICOM (0010x0010) Name", "DICOM (0010x0020) ID"]

        with open(f"logs/{filename}", "w") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(header)
            writer.writerow([])
            for line in self.log_list:
                writer.writerow(line)


def get_tag_data_from_xnat_header(dicom_header, tag_number: str):
    try:
        found_tag_dict = list(filter(lambda tag_dict: tag_dict['tag1'] == tag_number, dicom_header))[0]
    except IndexError as e:
        found_tag_value = "TAG EMPTY"
    else:
        found_tag_value = found_tag_dict['value']

    return found_tag_value


def get_date_time():
    now = str(datetime.datetime.now())
    date = now[:10].replace("-", "")
    time_slice = now[11:19].replace(":", "")

    return date, time_slice


def main():
    label, url, username, password = keystore.retrieve_entry_details()
    xnat_session.auth = (username, password)

    app = NameDiff(label, url)

    print(f"\nStarting name diff analysis on {label}")
    start = time.time()
    app.search_database()
    end = time.time()
    elapsed = round(end - start, 1)
    print(f"\nAnalysis Complete in {elapsed} seconds")


if __name__ == "__main__":
    with requests.Session() as xnat_session:
        main()
