import pydicom

file = ''

read_in = pydicom.read_file(file)

print(read_in, '\n')
# print(str(read_in['00291120'].value, 'utf-16'))
