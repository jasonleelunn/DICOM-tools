
version "6.1"

// XNAT Anonymisation Tool DicomEdit Script

// Author: Jason Lunn, The Institute of Cancer Research, UK

// DICOM Basic Application Level Confidentiality Profile Compliant

// Adapted from DICOM Standard, PS 3.15, Table E.1-1



newLabel := format["MOD_{0}", (3006,0002)]

(3006,0002) := newLabel


