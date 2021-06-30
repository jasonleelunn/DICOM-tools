#!/usr/bin/env python3

# Author: Jason Lunn, The Institute of Cancer Research, UK

from tkinter.filedialog import asksaveasfilename

import requests

import keystore.keystore as keystore


def get_patient_list(session, domain):
    project = input(f"Enter Project ID: ")
    patients = session.get(f'{domain}/data/projects/{project}/subjects')
    patient_json = patients.json()
    patient_label_list = []
    [patient_label_list.append(patient['label']) for patient in patient_json['ResultSet']['Result']]

    return project, patient_label_list


def session_edit(sessions):
    mod_sessions = []
    scanner_name = input("Enter scanner name: ")
    for session in sessions:
        mod_session = session[0][:16] + scanner_name
        mod_sessions.append((mod_session, session[1]))

    return mod_sessions


def save_output(lines):
    filename = asksaveasfilename(defaultextension=".csv")
    if not filename:
        print("File creation cancelled...")
        raise SystemExit
    else:
        with open(filename, 'w', newline='') as file:
            for item in lines:
                # file.write(f"{item[0], item[1]}\n")
                file.write(','.join(str(x) for x in item) + '\n')
        print(f"File Created!\nFile is located at '{filename}'")


def ask_session_modality():
    modality_input = input("Modality of session: ")
    modality = modality_input.lower()

    return modality


def main(session):
    label, dom, username, password = keystore.retrieve_entry_details()
    session.auth = (username, password)
    project, patient_list = get_patient_list(session, dom)
    # modality = ask_session_modality()
    modality = False

    sessions_label_dic = []
    for patient in patient_list:
        if modality:
            sessions = session.get(f'{dom}/data/projects/{project}'
                                   f'/subjects/{patient}/experiments?xsiType=xnat:{modality}SessionData')
        else:
            sessions = session.get(f'{dom}/data/projects/{project}'
                                   f'/subjects/{patient}/experiments')
        sessions_json = sessions.json()
        [sessions_label_dic.append((session['ID'], patient)) for session in sessions_json['ResultSet']['Result']]

    # sessions_label_dic = session_edit(sessions_label_dic)
    print(f"Number of sessions found: {len(sessions_label_dic)}")
    save_output(sessions_label_dic)


if __name__ == "__main__":
    with requests.Session() as requests_session:
        main(requests_session)
