#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import pydicom
import getpass
import requests
import tempfile
from pathlib import Path
import zipfile
import datetime
import csv


def read_seg(directory_path):
    files = list(Path(directory_path).rglob('*.dcm'))
    seg = pydicom.read_file(files[0], force=True)

    return seg


def get_number_of_frames(seg):
    # (0028, 0008) Number of Frames
    num_of_frames = seg['00280008'].value

    return int(num_of_frames)


def get_frame_size(seg):
    # (0028, 0010) Rows
    rows = seg['00280010'].value
    # (0028, 0011) Columns
    columns = seg['00280011'].value
    # (0028, 0101) Bits Stored
    bits_stored = seg['00280101'].value

    bits_per_frame = rows * columns * bits_stored
    bytes_per_frame = bits_per_frame / 8

    return int(bytes_per_frame)


def get_voxel_volume(seg):

    # (5200, 9229)  Shared Functional Groups Sequence
    tag_5200_9229 = seg['52009229'].value
    # (0028, 9110)  Pixel Measures Sequence
    tag_0028_9110 = tag_5200_9229[0]['00289110'].value
    # (0018, 0050) Slice Thickness
    tag_0018_0050 = tag_0028_9110[0]['00180050']
    # (0028, 0030) Pixel Spacing
    tag_0028_0030 = tag_0028_9110[0]['00280030']

    voxel_thickness = float(tag_0018_0050.value)
    (voxel_x, voxel_y) = tag_0028_0030.value

    voxel_volume = voxel_x * voxel_y * voxel_thickness
    voxel_dimensions = (voxel_x, voxel_y, voxel_thickness)

    return voxel_volume, voxel_dimensions


def get_segment_pixel_count(seg, start_byte, end_byte):
    # Pixel Data
    tag_7fe0_0010 = seg['7fe00010']

    frame_array = bytearray(tag_7fe0_0010.value)[start_byte:end_byte]
    bytes_as_bits = ''.join(format(byte, '08b') for byte in frame_array)

    zeros = bytes_as_bits.count("0")
    ones = bytes_as_bits.count("1")
    # print("0's", zeros)
    # print("1's", ones)
    # print(len(bytes_as_bits) - zeros, '\n')

    return int(ones)


def calculate_segment_volume(number_of_pixels, voxel_volume):
    segment_volume = float(number_of_pixels) * float(voxel_volume)
    return segment_volume


def find_volume(seg_data):
    segment_volumes = {}

    voxel_volume, voxel_dimensions = get_voxel_volume(seg_data)

    num_of_frames = get_number_of_frames(seg_data)
    bytes_per_frame = get_frame_size(seg_data)

    for frame in range(1, num_of_frames + 1):
        segment_end_byte = frame * bytes_per_frame
        segment_start_byte = segment_end_byte - bytes_per_frame

        pixel_count = get_segment_pixel_count(seg_data, segment_start_byte, segment_end_byte)
        segment_volume = calculate_segment_volume(pixel_count, voxel_volume)
        segment_volumes[frame] = segment_volume
        # exit()

    total_volume = sum(segment_volumes.values())
    # print(f"{total_segment_volume} mm^3")

    return segment_volumes, total_volume, voxel_dimensions


def get_login_details():

    domain = input(f"Enter XNAT Domain: ")
    username = input(f"Enter Username for {domain}: ")
    password = getpass.getpass(prompt=f"Enter Password for {username}@{domain}: ")

    return domain, username, password


def get_xnat_seg_list(session, domain, project_id):
    experiment_list_response = session.get(f"{domain}/data/projects/{project_id}/experiments")
    experiment_list_json = experiment_list_response.json()
    experiment_list = experiment_list_json['ResultSet']['Result']

    assessor_records_list = []

    for experiment in experiment_list:
        session_id = experiment['xnat:subjectassessordata/id']
        assessor_response = session.get(f"{domain}/data/experiments/{session_id}/assessors")
        assessor_response_json = assessor_response.json()
        assessor_records_count = assessor_response_json['ResultSet']['totalRecords']

        if assessor_records_count != "0":
            assessor_record_list = assessor_response_json['ResultSet']['Result']
            for assessor_record in assessor_record_list:
                # subject_id = experiment
                # assessor_record[]
                assessor_records_list.append(assessor_record)

    return assessor_records_list


def download_seg(xnat_session, domain, seg, temp_directory):
    session_id = seg['session_ID']
    assessor_id = seg['ID']
    assessor_response = xnat_session.get(f"{domain}/data/experiments/{session_id}/assessors/{assessor_id}"
                                         f"/resources/SEG/files?format=zip")
    # print(assessor_response.status_code)

    path_to_zipped_data = Path(f"{temp_directory}/{assessor_id}_zipped")
    path_to_data = Path(f"{temp_directory}/{assessor_id}")

    with open(path_to_zipped_data, 'wb') as file:
        file.write(assessor_response.content)
    with zipfile.ZipFile(path_to_zipped_data, 'r') as zip_file:
        zip_file.extractall(path_to_data)

    return path_to_data


def get_subject_name(xnat_session, domain, seg):
    session_id = seg['session_ID']
    assessor_response = xnat_session.get(f"{domain}/data/experiments/{session_id}?format=json")
    assessor_response_json = assessor_response.json()
    subject_name = assessor_response_json['items'][0]['data_fields']['dcmPatientName']

    return subject_name


def get_roi_label(xnat_session, domain, seg):
    session_id = seg['session_ID']
    assessor_id = seg['ID']
    assessor_response = xnat_session.get(f"{domain}/data/experiments/{session_id}/assessors/{assessor_id}?format=json")
    assessor_response_json = assessor_response.json()
    roi_label = assessor_response_json['items'][0]['data_fields']['name']

    return roi_label


def create_output_file(project_id):
    date = datetime.datetime.today().strftime('%Y-%m-%d_%H%M%S')
    filename = f"{date}_{project_id}_SEG_Volumes.csv"

    fieldnames = ["subject", "session", "ROI_label", "total_volume_(mm^3)", "voxel_dimensions_(x, y, z)"]

    with open(filename, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(fieldnames)

    return filename


def append_to_output_file(output_filename, subject_name, roi_label, seg_data, frame_volume_dictionary,
                          seg_total_volume, voxel_dimensions):
    session = seg_data['session_label']

    output_contents = {"subject": subject_name,
                       "session": session,
                       "ROI_label": roi_label,
                       "total_volume_(mm^3)": seg_total_volume,
                       "voxel_dimensions_(x, y, z)": voxel_dimensions}

    with open(f"{output_filename}", 'a') as f:
        dict_writer = csv.DictWriter(f, fieldnames=output_contents.keys())
        dict_writer.writerow(output_contents)


def download_from_xnat():
    domain, username, password = get_login_details()
    project_id = input("Enter target project ID: ")

    output_filename = create_output_file(project_id)

    with requests.Session() as xnat_session:
        xnat_session.auth = (username, password)
        seg_list = get_xnat_seg_list(xnat_session, domain, project_id)

        for seg in seg_list:
            with tempfile.TemporaryDirectory(dir="data/", prefix="seg_download_") as temp_location:
                seg_location = download_seg(xnat_session, domain, seg, temp_location)
                seg_data = read_seg(seg_location)
                frame_volume_dict, total_volume, voxel_dimensions = find_volume(seg_data)
                subject_name = get_subject_name(xnat_session, domain, seg)
                roi_label = get_roi_label(xnat_session, domain, seg)
                append_to_output_file(output_filename, subject_name, roi_label,
                                      seg, frame_volume_dict, total_volume, voxel_dimensions)


def local_file_test():
    testfile = Path("data")
    seg = read_seg(testfile)
    frame_volumes, total_volume, voxel_dims = find_volume(seg)


def main():
    download_from_xnat()
    # local_file_test()


if __name__ == "__main__":
    main()
