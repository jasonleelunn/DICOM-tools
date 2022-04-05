#!/usr/bin/env python3

import difflib

import pydicom


def main():
    file_1 = ''
    file_2 = ''

    header_1 = pydicom.read_file(file_1)
    prepped_1 = str(header_1).splitlines(keepends=True)
    header_2 = pydicom.read_file(file_2)
    prepped_2 = str(header_2).splitlines(keepends=True)

    diff = difflib.ndiff(prepped_1, prepped_2)
    print(''.join(diff))


if __name__ == "__main__":
    main()
