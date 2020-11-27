import pydicom

ds = pydicom.read_file("rtss_test/DICOM/anon_rtss.dcm", force=True)
# print(ds.dir("contour"))
# print(ds.ROIContourSequence[0])
print(ds)
