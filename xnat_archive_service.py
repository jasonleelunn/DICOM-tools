#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

"""
Script to auto archive project data in the XNAT prearchive with overwrite enabled
"""

import requests

import keystore.keystore as keystore


def get_project_prearchive_sessions(xnat_session, xnat_url, project_id):
    request = xnat_session.get(f"{xnat_url}/data/prearchive/projects/{project_id}")
    request_json = request.json()
    result = request_json['ResultSet']['Result']
    path_list = [entry['url'] for entry in result]

    return path_list


def archive_service_request(xnat_session, xnat_url, data_path):
    request = xnat_session.post(f"{xnat_url}/data/services/archive?{data_path}&overwrite=append")
    print(f"Response Code: {request.status_code}")


def create_data_source_param(path_list):
    full_string = ""
    for path in path_list:
        path_string = f"src={path}&"
        full_string += path_string

    # remove trailing ampersand
    output = full_string[0:-1]
    return output


def main():
    # get XNAT details
    xnat_label, url, username, password = keystore.retrieve_entry_details()

    project_id = input("Project ID: ")

    with requests.Session() as session:
        session.auth = (username, password)

        project_data_info = get_project_prearchive_sessions(session, url, project_id)

        data_source_string = create_data_source_param(project_data_info)

        archive_service_request(session, url, data_source_string)


if __name__ == "__main__":
    main()
