#!/usr/bin/env python3

"""
Script to scrape relevant DICOM Standard information from HTML tables and store them locally as JSON files

Author: Jason Lunn, The Institute of Cancer Research, UK
"""

import json

from bs4 import BeautifulSoup
import requests


def standard_sopclassuids():
    url = "http://dicom.nema.org/dicom/2013/output/chtml/part04/sect_B.5.html"

    html = requests.get(url).content
    soup = BeautifulSoup(html)
    table = soup.find_all('tbody')[0]

    data_dict = {}

    for row in table.find_all('tr'):
        name = row.find_all('td')[0].text
        uid = row.find_all('td')[1].text
        data = (name.strip('\n'), uid.strip('\n'))
        data_dict[f"{data}"] = False

    with open("/Users/jlunn/Desktop/sopclassuids.json", 'w') as json_file:
        json.dump(data_dict, json_file, indent=4)


def confidentiality_profiles():
    url = "https://dicom.nema.org/medical/dicom/current/output/html/part15.html#sect_E.1"

    html = requests.get(url).content
    soup = BeautifulSoup(html, features="lxml")
    table_link = soup.find('a', id='table_E.1-1')
    parent_div = table_link.parent
    table_body = parent_div.find('tbody')

    attribute_dict = {}
    table_headers = {0: 'attribute_name',
                     1: 'tag_number',
                     2: 'retired',
                     3: 'in_standard_composite_iod',
                     4: 'basic_profile',
                     5: 'retain_private',
                     6: 'retain_uids',
                     7: 'retain_device_id',
                     8: 'retain_institution_id',
                     9: 'retain_patient_characteristics',
                     10: 'retain_full_dates',
                     11: 'retain_modified_dates',
                     12: 'clean_descriptions',
                     13: 'clean_structured_content',
                     14: 'clean_graphical'}

    for row in table_body.find_all('tr'):
        row_dict = {}

        table_cells = row.find_all('td')
        for index, label in table_headers.items():
            data = table_cells[index].text
            row_dict[label] = data.strip('\n')

            if index == 1:
                tag_number = data.strip('\n')

        attribute_dict[tag_number] = row_dict

    with open("/Users/jlunn/Desktop/dicom_profiles.json", 'w') as json_file:
        json.dump(attribute_dict, json_file, indent=4)


def main():
    # standard_sopclassuids()
    confidentiality_profiles()


if __name__ == '__main__':
    main()
