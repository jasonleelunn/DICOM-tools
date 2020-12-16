import pydicom
from tkinter.filedialog import askopenfilename

input_file = askopenfilename(title="Select an RTSTRUCT file to analyse")
# input_file ="rtss_test/DICOM/anon_rtss.dcm"
ds = pydicom.read_file(input_file, force=True)

# print(ds.dir("contour"))
# print(ds.roiContourSequence[0])
# print(ds)


def get_roi_labels(file):
    labels = []

    if 'RTSTRUCT' in file.Modality:
        sequences = file.StructureSetfileSequence

        for sequence in sequences:
            label = sequence.fileName
            labels.append(label)
    else:
        msg = "The file object is not recognised as being RTS or SEG."
        raise Exception(msg)

    return labels


label_list = get_roi_labels(ds)
print(label_list)
