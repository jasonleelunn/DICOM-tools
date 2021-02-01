import os
import pydicom
from tkinter.filedialog import askopenfilename

# input_file = askopenfilename(title="Select an RTSTRUCT file to analyse")
# # input_file ="rtss_test/DICOM/anon_rtss.dcm"
# ds = pydicom.read_file(input_file, force=True)

# print(ds.dir("contour"))
# print(ds.roiContourSequence[0])
# print(ds)


def find_file(anon_id, folder):
    filepaths = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".dcm") and anon_id in file:
                filepaths.append(os.path.join(root, file))

    return filepaths


def get_roi_labels(input_file):
    labels = []
    file = pydicom.read_file(input_file, force=True)
    modality = file.Modality

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
    # rtss_folder = "rtss_test"
    rtss_folder = "extracted/Batch2_full"
    patient_num = input("Enter anonymous ID number: ")
    patient_id = f"RS-5293-{patient_num}"
    files = find_file(patient_id, rtss_folder)
    for file in files:
        label_list, modality = get_roi_labels(file)
        print(label_list)
        if 'RTSTRUCT' in modality:
            ds = pydicom.read_file(file, force=True)
            # print(ds)
            info_sequence = ds.StructureSetROISequence
            # print(info_sequence)

            contour_sequence = ds.ROIContourSequence
            for seq in contour_sequence:
                if seq.ReferencedROINumber:
                    try:
                        contour = seq.ContourSequence
                    except AttributeError as e:
                        num = seq.ReferencedROINumber
                        roi_name = seq.ReferencedROILabel
                        print(f"{roi_name} is empty")
                        print(e)

            # number = thing.ReferencedROINumber
            # print("\n", file[22:33])
            for seq in info_sequence:
                print(seq.ROINumber, seq.ROIName)


if __name__ == "__main__":
    main()


# rtss_folder = "extracted"
# patient_num = input("Enter anonymous ID number: ")
# patient_id = f"RS-5293-{patient_num}"
# files = find_file(patient_id)
#
# for filepath in files:
#     label_list = get_roi_labels(filepath)
#     if label_list:
#         print(f"\n{label_list}")
