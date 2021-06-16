import os
import pathlib

import pydicom
import numpy as np
import array
from tkinter.filedialog import askopenfilename, askdirectory

# input_file = askopenfilename(title="Select an RTSTRUCT file to analyse")
# # input_file ="rtss_test/DICOM/anon_rtss.dcm"
# ds = pydicom.read_file(input_file, force=True)

# print(ds.dir("contour"))
# print(ds.roiContourSequence[0])
# print(ds)


def find_file(folder):
    filepaths = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".dcm"):
                filepaths.append(os.path.join(root, file))

    return filepaths


def get_roi_labels(input_file):
    labels = []
    file = pydicom.read_file(input_file, force=True)
    # print(file)
    modality = file.Modality
    # print(modality)

    if 'RTSTRUCT' in modality:
        sequences = file.StructureSetROISequence

        for sequence in sequences:
            label = sequence.ROIName
            labels.append(label)
    else:
        msg = "The file object is not recognised as being RTS or SEG."
        # raise Exception(msg)

    return labels, modality


def main():
    rtss_folder = pathlib.Path(askdirectory())

    files = find_file(rtss_folder)
    for file in files:
        label_list, modality = get_roi_labels(file)
        ds = pydicom.read_file(file, force=True)
        try:
            # print(file)
            # split_file = file.split("/")
            # filename = split_file[-1][4:20]
            # filename = split_file[5]
            print(ds)
            exit()
            # print(label_list)

            # print(ds['00640002'][0]['00640005'][0]['00640009'])
            # print(ds['00640002'][0]['00640005'][0]['00640007'])
            # original_array = ds['00640002'][0]['00640005'][0]['00640009'].value
            # # new_array = np.array(original_array)
            #
            # new_array = array.array('f', original_array)
            # print(min(new_array), max(new_array))
        except KeyError as e:
            print("tag not found")


if __name__ == "__main__":
    main()
