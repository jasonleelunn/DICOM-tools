#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

"""
Script to analyse an entire XNAT archive for Secondary Capture and Presentation State Modalities, and scan sets which
may contain burnt-in PHI in the image pixel data.
"""

import re
import csv
import datetime
import pydicom.errors
from pydicom.uid import UID
import xnat
import requests
import time
from progress.bar import ChargingBar


def user_pass_data(which_xnat):
    u = None
    pw = None

    dom = input(f"Enter {which_xnat} XNAT domain (e.g. http://example.xnat.org): ")
    code = 0
    while not code == 200 or code == 403:
        u = input(f"Enter {which_xnat} XNAT Username: ")
        pw = input(f"Enter {which_xnat} XNAT Password: ")
        check = requests.get(f'{dom}', auth=(u, pw))
        code = check.status_code
        # print(code)
        if code == 200 or code == 403:
            print(f"Successful Login to {which_xnat} XNAT.")
        else:
            print("Could not verify credentials with XNAT. Please try again.")
    return dom, u, pw


class FancyBar(ChargingBar):
    message = 'Scanning'
    fill = '#'
    suffix = '%(percent).1f%% - Estimated Time Remaining: %(eta)ds'


class App:
    def __init__(self):
        self.report_table_list = []
        self.log_list = []

        # SOPClassUIDs to compare metadata against
        self.secondary_capture_uid = "1.2.840.10008.5.1.4.1.1.7"
        self.presentation_state_uid = "1.2.840.10008.5.1.4.1.1.11"
        # self.ct_uid = "1.2.840.10008.5.1.4.1.1.1"
        # self.mr_uid = "1.2.840.10008.5.1.4.1.1.4"

    def xnat_loop(self):
        source_dom, source_u, source_pw = user_pass_data("Source")
        # source_dom = "http://xnatdev.xnat.org"
        # source_u = "admin"
        # source_pw = ""

        with xnat.connect(source_dom, user=source_u, password=source_pw) as connection:
            xnat_projects = connection.projects
            print(f"Found {len(xnat_projects)} projects in XNAT database.\n")

            with FancyBar('Analysing Database', max=len(xnat_projects)) as bar:
                for project in xnat_projects:
                    xnat_subjects = xnat_projects[project].subjects
                    for patient in xnat_subjects:
                        xnat_experiments = xnat_subjects[patient].experiments
                        for session in xnat_experiments:
                            xnat_scans = xnat_experiments[session].scans
                            for scan in xnat_scans:
                                scan_data = xnat_scans[scan]
                                self.sop_class_uid_check(scan_data)
                    bar.next()

        date, time_slice = get_date_time()
        if self.report_table_list:
            self.write_report(date, time_slice)
        if self.log_list:
            self.write_log(date, time_slice)

    def sop_class_uid_check(self, scan_data):
        try:
            dicom_header = scan_data.read_dicom()
        except ValueError as e:
            # print(f"Scan {scan_data.id} in session {scan_data.image_session_id} is not a DICOM resource")
            self.non_dicom_log(scan_data, e)
        except pydicom.errors.InvalidDicomError as e:
            self.non_dicom_log(scan_data, e)
        except IndexError as e:
            # issue with mixin package in XNATpy
            self.non_dicom_log(scan_data, e)

        else:
            sop_class_uid_tag = dicom_header['00080016'].value
            uid_info = UID(sop_class_uid_tag)
            burned_in_annotation_tag = "#TAG-NOT-FOUND#"
            try:
                burned_in_annotation_tag = dicom_header['00280301'].value
            except KeyError:
                pass

            burnt_tag_check = re.search(re.escape("YES"), burned_in_annotation_tag, flags=re.IGNORECASE)
            if self.secondary_capture_uid in uid_info or burnt_tag_check:
                # or self.presentation_state_uid in uid_info
                self.scan_location_info(scan_data, uid_info, burned_in_annotation_tag)

    def scan_location_info(self, scan_data, uid_info, burned_tag_contents):
        project = scan_data.project
        session_id = scan_data.image_session_id
        scan_name = scan_data.id

        uid_name = uid_info.name

        line = [project, session_id, scan_name, uid_name, burned_tag_contents]
        self.report_table_list.append(line)

    def write_report(self, date, time_slice):
        filename = f"{date}_{time_slice}_secondary_capture_report.csv"
        header = ["Project ID", " Session ID", " Scan ID", " SOPClassUID Name", " Tag (0028:0301) Contents"]

        with open(f"logs/{filename}", "w") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(header)
            writer.writerow([])
            for line in self.report_table_list:
                writer.writerow(line)

    def non_dicom_log(self, scan_data, error_details):
        project = scan_data.project
        session_id = scan_data.image_session_id
        scan_name = scan_data.id

        line = [project, session_id, scan_name, error_details]
        self.log_list.append(line)

    def write_log(self, date, time_slice):
        filename = f"{date}_{time_slice}_secondary_capture_log.csv"
        header = ["Project ID", " Session ID", " Scan ID", " Error Details"]

        with open(f"logs/{filename}", "w") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(header)
            writer.writerow([])
            for line in self.log_list:
                writer.writerow(line)


def get_date_time():
    now = str(datetime.datetime.now())
    date = now[:10].replace("-", "")
    time_slice = now[11:19].replace(":", "")

    return date, time_slice


def main():
    app = App()

    start = time.time()
    app.xnat_loop()
    end = time.time()
    elapsed = round(end - start, 1)
    print(f"\nAnalysis Complete in {elapsed} seconds")
    print(f"Found {len(app.report_table_list)} potential burnt-in PHI scan sets, see readout in logs/ for details\n")


if __name__ == "__main__":
    main()
