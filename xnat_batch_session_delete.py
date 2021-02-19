#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

"""
Script to mass delete a selection of scan sessions from XNAT
"""

import time
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
    message = 'Removing Data'
    fill = '#'
    suffix = '%(percent).1f%% - Estimated Time Remaining: %(eta)ds'


class App:
    def __init__(self, session, domain):
        self.session = session
        self.domain = domain

    def api_delete_call(self, experiment_id, scan_id):
        self.session.delete(f"{self.domain}/data/experiments/{experiment_id}/scans/{scan_id}")


def main():
    domain, username, password = user_pass_data("Target")

    with requests.Session() as session:
        session.auth = (f'{username}', f'{password}')
        app = App(session, domain=domain)

    start = time.time()
    # app.xnat_loop()
    end = time.time()
    elapsed = round(end - start, 1)
    print(f"Ran in {elapsed} seconds\n")


if __name__ == "__main__":
    main()
