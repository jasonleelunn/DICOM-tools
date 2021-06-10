#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

import pykeepass
import getpass
import pathlib
import argparse
import pprint


class PasswordDatabase:
    def __init__(self):
        self.database_location = "keystore.kdbx"
        self.database_instance = None
        self.master_password = None

        self.check_keypass_db_exist()

    def get_master_password(self):
        self.master_password = getpass.getpass(prompt="Enter Master Password: ")

    def create_master_password(self):
        first_password_input = getpass.getpass(prompt="Enter a Master Password: ")
        second_password_input = getpass.getpass(prompt="Enter the Master Password again: ")
        if first_password_input == second_password_input:
            self.master_password = first_password_input
        else:
            print("Passwords do not match, please try again.")
            self.create_master_password()

    def check_keypass_db_exist(self):
        if pathlib.Path(self.database_location).exists():
            self.get_master_password()
            self.read_keypass_db()
        else:
            self.create_master_password()
            self.initialise_keypass_db()

    def initialise_keypass_db(self):
        self.database_instance = pykeepass.create_database(filename=self.database_location,
                                                           password=self.master_password)

    def read_keypass_db(self):
        try:
            self.database_instance = pykeepass.PyKeePass(filename=self.database_location,
                                                         password=self.master_password)
        except pykeepass.exceptions.CredentialsError as e:
            print("Incorrect master password, please try again.")
            self.get_master_password()
            self.read_keypass_db()

    def add_keypass_entry(self, entry_label, entry_url, entry_username, entry_password):
        self.database_instance.add_entry(self.database_instance.root_group,
                                         entry_label, entry_username, entry_password, url=entry_url)
        self.database_instance.save()

    def delete_keypass_entry(self, entry):
        self.database_instance.delete_entry(entry)
        self.database_instance.save()


def get_new_entry_details():
    label = input("Enter Label: ")
    domain = input("Enter Domain: ")
    username = input(f"Enter Username for {domain}: ")
    password = getpass.getpass(prompt=f"Enter Password for {username}@{domain}: ")

    return label, domain, username, password


def retrieve_entry_details():
    keystore = PasswordDatabase()
    entries = keystore.database_instance.entries
    entries_id = {index: entry for index, entry in enumerate(entries)}

    pretty = pprint.PrettyPrinter(width=30)
    pretty.pprint(entries_id)

    selected_id = int(input("Enter the index of the entry to retrieve from the keystore: "))
    selected_entry = entries_id[selected_id]

    label = selected_entry.title
    url = selected_entry.url
    username = selected_entry.username
    password = selected_entry.password

    return label, url, username, password


def main():
    keystore = PasswordDatabase()

    if args.add_new:
        entry_label, entry_domain, entry_username, entry_password = get_new_entry_details()
        keystore.add_keypass_entry(entry_label, entry_domain, entry_username, entry_password)

    entries = keystore.database_instance.entries
    entries_id = {index: entry for index, entry in enumerate(entries)}
    print(entries_id)

    if args.delete:
        delete_id = int(input("Enter the index of the entry to delete from the keystore: "))
        entry_for_deletion = entries_id[delete_id]
        keystore.delete_keypass_entry(entry_for_deletion)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create, view and modify a KeyPassX keystore database")

    parser.add_argument("-a", "--add_new",
                        help="add a new entry to the keystore", default=False, action='store_true')
    parser.add_argument("-v", "--view",
                        help="view all entries currently in the keystore", default=False, action='store_true')
    parser.add_argument("-d", "--delete",
                        help="delete an entry from the keystore", default=False, action='store_true')

    args = parser.parse_args()

    main()
