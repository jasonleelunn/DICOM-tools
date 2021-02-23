#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

"""
Script to mass delete a selection of scan sessions from XNAT
"""

import csv
from tkinter.filedialog import askopenfilename
import time
import requests
from progress.bar import ChargingBar
import logging
import datetime

# setup logging
datetime = datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
log_path = f"logs/{datetime}_batch_deletion.log"
logging.basicConfig(filename=log_path, filemode='w', format='%(asctime)s %(message)s', level=logging.INFO)


# simple CLI interface to get XNAT login credentials
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
        if code == 200 or code == 403:
            print(f"Successful Login to {which_xnat} XNAT.")
        else:
            print("Could not verify credentials with XNAT. Please try again.")
    return dom, u, pw


class FancyBar(ChargingBar):
    message = 'Removing Data'
    fill = '#'
    suffix = '%(percent).1f%% - Estimated Time Remaining: %(eta)ds'


class App:
    def __init__(self, session, domain, search_data_header, search_data):
        self.session = session
        self.domain = domain
        self.search_data_header = search_data_header
        self.search_data = search_data

    def extract_input_data(self):
        print(self.search_data)

    def api_delete_call(self, experiment_id, scan_id):
        try:
            delete_request = self.session.delete(f"{self.domain}/data/experiments/{experiment_id}/scans/{scan_id}")

            if delete_request.status_code == 200:
                logging.info(f"Successfully deleted scan {scan_id} in session {experiment_id}")
            elif delete_request.status_code == 404:
                logging.warning(f"Unable to find scan {scan_id} in session {experiment_id}")
            else:
                logging.warning(f"Unexpected response from XNAT with http code {delete_request.code} "
                                f"for scan {scan_id} in session {experiment_id}:\n"
                                f"{delete_request.text}")
        except Exception as e:
            logging.warning(f"Exception occurred while processing scan {scan_id} "
                            f"in session {experiment_id} as follows:\n {e}")

    def delete_data(self):
        with FancyBar("Removing Data", max=len(self.search_data)) as bar:
            for line in self.search_data:
                self.api_delete_call(line['Session ID'], line['Scan ID'])
                bar.next()
                # print(f"Deleting scan set {line['Scan ID']} from session
                # {line['Session ID']} in project {line['Project ID']}")


def read_input_file():
    file = askopenfilename(title="Select input CSV file")
    with open(file, 'r') as input_file:
        reader = csv.DictReader(input_file, delimiter=',', skipinitialspace=True)
        fields = reader.fieldnames
        lists_out = [row for row in reader]

    return fields, lists_out


def main():
    domain, username, password = user_pass_data("Target")
    input_data_fields, input_data_rows = read_input_file()

    with requests.Session() as session:
        session.auth = (f'{username}', f'{password}')
        app = App(session=session, domain=domain,
                  search_data_header=input_data_fields, search_data=input_data_rows)

        start = time.time()
        app.delete_data()
        end = time.time()
        elapsed = round(end - start, 1)
        print(f"\nRan in {elapsed} seconds")
        print("Deletion complete.\n")


if __name__ == "__main__":
    main()
