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
    message = 'Scanning'
    fill = '#'
    suffix = '%(percent).1f%% - Estimated Time Remaining: %(eta)ds'


def api_delete_call():
    pass


def main():
    app = App()

    start = time.time()
    app.xnat_loop()
    end = time.time()
    elapsed = round(end - start, 1)


if __name__ == "__main__":
    main()
