#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import csv
import datetime
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

    def xnat_loop(self):
        # source_dom, source_u, source_pw = user_pass_data("Source")
        source_dom = "http://xnatdev.xnat.org"
        source_u = "admin"
        source_pw = "TCIABigMemes"

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

        if self.report_table_list:
            self.write_report()

    def sop_class_uid_check(self, scan_data):

        dicom_header = scan_data.read_dicom()
        sop_class_uid = dicom_header['00080016'].value
        uid_info = UID(sop_class_uid)
        # print(uid_info.name)

        secondary_capture_uid = "1.2.840.10008.5.1.4.1.1.7"
        # ct_uid = "1.2.840.10008.5.1.4.1.1.1"
        # mr_uid = "1.2.840.10008.5.1.4.1.1.4"

        if secondary_capture_uid in uid_info:
        # if mr_uid in uid_info:
            # print("Secondary Capture Detected")
            self.scan_location_info(scan_data)

    def scan_location_info(self, scan_data):
        project = scan_data.project
        session_id = scan_data.image_session_id
        scan_name = scan_data.id
        line = [project, session_id, scan_name]
        self.report_table_list.append(line)

    def write_report(self):
        now = str(datetime.datetime.now())
        date = now[:10].replace("-", "")
        time = now[11:19].replace(":", "")

        filename = f"{date}_{time}_secondary_capture_report.csv"
        header = ["Project ID", "Session ID", "Scan ID"]

        with open(f"logs/{filename}", "wb") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(header)
            for line in self.report_table_list:
                writer.writerow(line)


def main():
    app = App()

    start = time.time()
    app.xnat_loop()
    end = time.time()
    elapsed = end - start
    print(f"Analysis Complete in {elapsed} seconds.\n")
    print(f"Found {len(app.report_table_list)} secondary capture modality scan sets\n")


if __name__ == "__main__":
    main()
