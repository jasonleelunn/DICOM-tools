import os
import pydicom
from tkinter.filedialog import askopenfilename

# input_file = askopenfilename(title="Select an RTSTRUCT file to analyse")
# # input_file ="rtss_test/DICOM/anon_rtss.dcm"
# ds = pydicom.read_file(input_file, force=True)

# print(ds.dir("contour"))
# print(ds.roiContourSequence[0])
# print(ds)


def find_file(anon_id):
    filepaths = []
    for root, dirs, files in os.walk(rtss_folder):
        for file in files:
            if file.endswith(".dcm") and anon_id in file:
                filepaths.append(os.path.join(root, file))

    return filepaths


def get_roi_labels(input_file):
    labels = []
    file = pydicom.read_file(input_file, force=True)

    if 'RTSTRUCT' in file.Modality:
        sequences = file.StructureSetROISequence

        for sequence in sequences:
            label = sequence.ROIName
            labels.append(label)
    else:
        msg = "The file object is not recognised as being RTS or SEG."
        # raise Exception(msg)

    return labels


rtss_folder = "rtss_test"
patient_num = input("Enter anonymous ID number: ")
patient_id = f"RS-5293-{patient_num}"
files = find_file(patient_id)

for filepath in files:
    label_list = get_roi_labels(filepath)
    if label_list:
        print(f"\n{label_list}")
