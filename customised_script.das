
version "6.1"

// XNAT Anonymisation Tool DicomEdit Script

// Author: Jason Lunn, The Institute of Cancer Research, UK

// DICOM Basic Application Level Confidentiality Profile Compliant

// Adapted from DICOM Standard, PS 3.15, Table E.1-1


// Script to only clean files of Private Manufacturer specific tags


describe scanDate1 hidden
describe scanDate2 hidden
scanDate1 := format["{0}", (0008,0020)]
scanDate2 := replace[scanDate1, "null", "noDate"]

describe scanTime1 hidden
describe scanTime2 hidden
scanTime1 := format["{0}", (0008,0030)]  
scanTime2 := substring[replace[scanTime1, "null", "noTime"], 0, 6]

describe scannerName1 hidden
describe scannerName2 hidden
scannerName1 := format["_{0}", (0008,1090)]
scannerName2 := replace[scannerName1, "_null", ""]


removeAllPrivateTags

(0010,0010) := "WEEEEEEE" // Anonymised Patient Name

project := "Unassigned"

session := format["{0}_{1}{2}", scanDate2, scanTime2, scannerName2]

(0010,4000) := format["Project: Unassigned; Subject: WEEEEEEE; Session: {0}; AA:True", session] // Patient Comments
