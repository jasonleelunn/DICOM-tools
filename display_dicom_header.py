import pydicom

file = ''

read_in = pydicom.read_file(file)

print(read_in, '\n')

# read-in Siemens EditCorrect byte field
# print(str(read_in['00291120'].value, 'utf-16'))
