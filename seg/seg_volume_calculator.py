#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import pydicom


def read_seg(file):
    seg = pydicom.read_file(file, force=True)
    # print(seg)

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

    return voxel_volume


def get_segment_pixel_count(seg, start_byte, end_byte):
    # Pixel Data
    tag_7fe0_0010 = seg['7fe00010']

    frame_array = list(tag_7fe0_0010.value)[start_byte:end_byte]
    # frame_array = [elem / 255 for elem in frame_array]
    print("0's", frame_array.count(0))
    print("1's", frame_array.count(1))
    # print(set(frame_array))

    return len(frame_array) - frame_array.count(0)


def calculate_segment_volume(number_of_pixels, voxel_volume):
    segment_volume = float(number_of_pixels) * float(voxel_volume)
    return segment_volume


def main():
    test_file = "data/SEG_20210404_165148.dcm"
    seg_data = read_seg(test_file)
    segment_volumes = {}

    voxel_volume = get_voxel_volume(seg_data)

    num_of_frames = get_number_of_frames(seg_data)
    bytes_per_frame = get_frame_size(seg_data)

    for frame in range(1, num_of_frames + 1):
        segment_end_byte = frame * bytes_per_frame
        segment_start_byte = segment_end_byte - bytes_per_frame
        pixel_count = get_segment_pixel_count(seg_data, segment_start_byte, segment_end_byte)
        segment_volume = calculate_segment_volume(pixel_count, voxel_volume)
        segment_volumes[frame] = segment_volume
        exit()


if __name__ == "__main__":
    main()
