import pydicom

ds = pydicom.read_file("rtstruct.dcm", force=True)
ds.dir("contour")
