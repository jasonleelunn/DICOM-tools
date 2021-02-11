#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import pydicom
from pydicom.uid import UID
import xnat
import requests
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


def main():
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
                            sop_class_uid_check(scan_data)
                bar.next()


def sop_class_uid_check(scan_data):

    dicom_header = scan_data.read_dicom()
    sop_class_uid = dicom_header['00080016'].value
    uid_info = UID(sop_class_uid)
    # print(uid_info.name)

    secondary_capture_uid = "1.2.840.10008.5.1.4.1.1.7"
    # ct_uid = "1.2.840.10008.5.1.4.1.1.1"
    mr_uid = "1.2.840.10008.5.1.4.1.1.4"

    # if secondary_capture_uid in uid_info:
    if mr_uid in uid_info:
        # print("Secondary Capture Detected")
        scan_location_info(scan_data)


def scan_location_info(scan_data):
    project = scan_data.project
    session_id = scan_data.image_session_id
    scan_name = scan_data.id


if __name__ == "__main__":
    main()
