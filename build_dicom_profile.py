#!/usr/bin/env python3

"""
Script to create DicomEdit version 6+ conformant .das files from a JSON containing information from Table E1.1 in
PS3.15 of the DICOM Standard, Application Confidentiality Profile Attributes

Author: Jason Lunn, The Institute of Cancer Research, UK
"""

import datetime
import json

"""
De-identification Action Codes (The DICOM Standard PS3.15 Table E.1-1a.)

D - replace with a non-zero length value that may be a dummy value and consistent with the VR
Z - replace with a zero length value, or a non-zero length value that may be a dummy value and consistent with the VR
X - remove
K - keep (unchanged for non-sequence attributes, cleaned for sequences)
C - clean, replace with values of similar meaning known not to contain identifying information, consistent with the VR
U - replace with a non-zero length UID that is internally consistent within a set of Instances

"""

option_descriptions = {'retain_private': "Retain Safe Private Option",
                       'retain_uids': "Retain UIDs Option",
                       'retain_device_id': "Retain Device Identity Option",
                       'retain_institution_id': "Retain Institution Identity Option",
                       'retain_patient_characteristics': "Retain Patient Characteristics Option",
                       'retain_full_dates': "Retain Longitudinal Temporal Information with Full Dates Option",
                       'retain_modified_dates': "Retain Longitudinal Temporal Information with Modified Dates Option",
                       'clean_descriptions': "Clean Descriptors Option",
                       'clean_structured_content': "Clean Structured Content Option",
                       'clean_graphical': "Clean Graphics Option"}


def read_json(json_filepath):
    with open(json_filepath, 'r') as file:
        json_dict = json.load(file)

    return json_dict


def create_profile_header(version, profile_options):
    today = datetime.date.today()
    header_text = f"""version \"{version}\"
                        
// DICOM Basic Application Level Confidentiality Profile
// for use with the XNAT Anonymisation Tool

// Created by Jason L. Lunn 
// Generated on {today.strftime("%d %B %Y")}


"""
    if profile_options:

        options = "\n".join(f"// {option_descriptions[profile]}" for profile in profile_options)

        options_text = f"""// --- Profile Options Enabled ---
        
{options}


"""
        header_text = header_text + options_text

    return header_text


def create_profile_footer(profile_choices):
    if 'retain_private' not in profile_choices:
        remove_private_str = "removeAllPrivateTags"
    else:
        remove_private_str = ""
    footer_text = f"""
{remove_private_str}
"""

    return footer_text


def build_attribute_modifications(attribute_dict, profile_choices):
    attribute_output = []
    for attribute in attribute_dict.values():

        profile_action_code = attribute['basic_profile']

        for profile in profile_choices:
            # only change code if it is not already set to C (Clean)
            if profile_action_code != 'C' and attribute[profile]:
                profile_action_code = attribute[profile]

        modification_str = None
        # type 1 tags
        if 'D' in profile_action_code:
            if 'SQ' in attribute['VR']:
                modification_str = f"{attribute['tag_number']}[*] := \"Anon\""
            else:
                modification_str = f"{attribute['tag_number']} := \"Anon\""
        # type 2 tags
        elif 'Z' in profile_action_code:
            modification_str = f"{attribute['tag_number']} := \"\""
        # type 3 tags
        elif 'X' in profile_action_code:
            modification_str = f"- {attribute['tag_number']}"

        if modification_str is not None:
            line = f"{modification_str} // {attribute['attribute_name']}\n"
            attribute_output.append(line)

    return attribute_output


def save_output_file(header="", body=None, footer=""):
    with open("/Users/jlunn/Desktop/test.das", 'w') as file:
        file.write(header)
        file.writelines(body)
        file.write(footer)


def main():
    filepath = '/Users/jlunn/Desktop/dicom_profiles.json'
    attribute_dict = read_json(filepath)

    profile_choices = [
        # 'retain_private',
        'retain_uids',
        # 'retain_patient_characteristics',
        'retain_full_dates',
        # 'retain_device_id'
    ]

    dicomedit_version = "6.1"

    head_text = create_profile_header(dicomedit_version, profile_choices)
    body_text = build_attribute_modifications(attribute_dict, profile_choices)
    extra_text = create_profile_footer(profile_choices)

    save_output_file(head_text, body_text, extra_text)


if __name__ == '__main__':
    main()
