import requests

reg_data = {
    "username": "err_test",
    "password": "Password123!",
    "nickname": "Tester",
    "email": "err@example.com"
}
try:
    r = requests.post("http://localhost:8000/api/auth/register", json=reg_data)
    print("Status:", r.status_code)
    print("Body:", r.text)
except Exception as e:
    print(e)
