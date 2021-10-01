#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

"""
Script to export all user info from XNAT system
"""

import csv
import datetime

import requests

import keystore.keystore as keystore


def print_active_users(session, url):
    request = session.get(f"{url}/xapi/users/active")
    user_list = request.json()

    print(list(user_list.keys()))


def get_user_list(session, url):
    # modern way, XNAT with xapi enabled
    request = session.get(f"{url}/xapi/users/current")
    user_list = request.json()
    return user_list


def get_user_list_deprecated(session, url):
    # deprecated way, XNAT older than 1.7.x
    request = session.get(f"{url}/data/users")
    user_list_json = request.json()
    user_list = user_list_json['ResultSet']['Result']
    return user_list


def filter_user_list(is_deprecated, user_list, data_fields):
    filtered_list = []
    for user in user_list:
        if is_deprecated:
            filtered_list.append([user[data_field] for data_field in data_fields])
        else:
            if user['enabled']:
                filtered_list.append([user[data_field] for data_field in data_fields])
    return filtered_list


def write_to_csv(info_list, xnat_label):
    date = datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"{date}_{xnat_label}_user_info.csv"
    with open(f"extracted/{filename}", "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for user in info_list:
            writer.writerow(user)


def main():
    # get XNAT details
    xnat_label, url, username, password = keystore.retrieve_entry_details()

    # choose user fields to extract (list of strings of arbitrary length)
    user_data_fields = ['email']

    with requests.Session() as session:
        session.auth = (username, password)

        is_deprecated = input("Deprecated XNAT version (less than 1.7.x)? "
                              "[Press Return for false, type anything else for true]: ")

        if not is_deprecated:

            print_active_users(session, url)
            exit(0)

            user_list = get_user_list(session, url)
        else:
            user_list = get_user_list_deprecated(session, url)

        filtered_list = filter_user_list(is_deprecated, user_list, user_data_fields)
        write_to_csv(filtered_list, xnat_label)


if __name__ == "__main__":
    main()
