import requests

url = 'http://localhost:8000/student_register'
data = {
    'name': 'Test User',
    'loginid': 'TEST999',
    'mobile': '1234567890',
    'password': 'password123',
    'department': 'CSE',
    'year': '1',
    'semester': '1',
    'section': 'A'
}

files = []
for i in range(15):
    files.append(('images', (f'img_{i}.jpg', b'dummydata_face', 'image/jpeg')))

try:
    response = requests.post(url, data=data, files=files)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print('Error:', e)
