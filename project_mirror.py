#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import requests
import xnat
from progress.bar import Bar


@contextmanager
def suppress_stderr():
    with open(os.devnull, "w") as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr


def anon_insertion(anon_name, script_path):
    # (0010,0010) DICOM tag
    new_name = f"\n(0010,0010) := \"{anon_name}\" // Anonymised Patient Name\n"
    # (0010,0020) DICOM tag
    new_id = f"\n(0010,0020) := \"{anon_name}\" // Anonymised Patient ID\n"

    with open(script_path, 'r') as standard_script:
        content = standard_script.read()

    custom_script_path = "customised_script.das"
    with open(custom_script_path, 'w') as custom_script:
        custom_script.write(content)
        custom_script.write(new_name)
        custom_script.write(new_id)

    return custom_script_path


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


def download(directory, xnat_scans, scan):

    # xnat_project = connection.projects[project_id]
    # xnat_subject = xnat_project.subjects[subject]
    xnat_scan = xnat_scans[scan]
    xnat_scan.download_dir(directory, verbose=False)
    shutil.make_archive(directory, 'zip', directory)


def upload(domain, username, password, directory):
    with requests.Session() as session:
        session.auth = (username, password)
        subject_upload = session.post(f'{domain}/data/services/import?inbody=true&import-handler=DICOM-zip'
                                      f'&dest=/archive', data=open(f"{directory}.zip", 'rb'))


class FancyBar(Bar):
    message = 'Loading'
    fill = '#'
    suffix = '%(percent).1f%% - Estimated Time Remaining: %(eta)ds'


def main():
    source_dom, source_u, source_pw = user_pass_data("Source")
    target_dom, target_u, target_pw = user_pass_data("Target")

    with xnat.connect(source_dom, user=source_u, password=source_pw) as subject_connection:
        while True:
            try:
                project_id = input("Enter a project ID to mirror on the target XNAT instance: ")
                xnat_project = subject_connection.projects[project_id]
                xnat_subjects = xnat_project.subjects
                print(f"Number of subjects found in project: {len(xnat_subjects)}")
            except KeyError:
                print(f"Project with ID \"{project_id}\" not found!\nPlease try again.\n")
            else:
                break

    with FancyBar('Copying Project...', max=len(xnat_subjects)) as bar:
        with xnat.connect(source_dom, user=source_u, password=source_pw) as connection:
            xnat_project = connection.projects[project_id]
            for patient in xnat_subjects:
                xnat_experiments = xnat_project.subjects[patient].experiments
                for session in xnat_experiments:
                    xnat_scans = xnat_project.subjects[patient].experiments[session].scans
                    for scan in xnat_scans:
                        temp_dir = Path("temp/")
                        with tempfile.TemporaryDirectory(dir=temp_dir, prefix="project_mirror_") as dir_path:
                            download(dir_path, xnat_scans, scan)
                            upload(target_dom, target_u, target_pw, dir_path)

                bar.next()


if __name__ == "__main__":
    main()
