import json

from bs4 import BeautifulSoup
import requests


def standard_sopclassuids():
    url = "http://dicom.nema.org/dicom/2013/output/chtml/part04/sect_B.5.html"

    html = requests.get(url).content
    soup = BeautifulSoup(html)
    table = soup.find_all('tbody')[0]

    data_dict = {}

    for row in table.find_all('tr'):
        name = row.find_all('td')[0].text
        uid = row.find_all('td')[1].text
        data = (name.strip('\n'), uid.strip('\n'))
        data_dict[f"{data}"] = False

    with open("/Users/jlunn/Desktop/sopclassuids.json", 'w') as json_file:
        json.dump(data_dict, json_file)


def main():
    standard_sopclassuids()


if __name__ == '__main__':
    main()
