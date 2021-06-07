
version "6.1"

// XNAT Anonymisation Tool DicomEdit Script

// Author: Jason Lunn, The Institute of Cancer Research, UK

// DICOM Basic Application Level Confidentiality Profile Compliant

// Adapted from DICOM Standard, PS 3.15, Table E.1-1



// newLabel := "ALT_structureSet"

// (3006,0002) := newLabel

date := (3006,0008)
time := (3006,0009)

(0008,0020) := date
(0008,0030) := time
