#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import keystore.keystore as keystore


def main():
    label, url, username, password = keystore.retrieve_entry_details()


if __name__ == "__main__":
    main()
