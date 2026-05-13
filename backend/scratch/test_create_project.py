import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_create():
    # 1. Login to get token (using common default or previous knowledge)
    # Since I don't have the user's password, I'll try to use a mock or check the database
    # But wait, I can just create a temporary test user
    
    reg_data = {
        "username": "testuser_" + str(int(time.time())),
        "password": "Password123!",
        "nickname": "Tester",
        "email": "test@example.com"
    }
    
    print("Step 1: Registering test user...")
    r = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
    if r.status_code != 200:
        print(f"Register failed: {r.text}")
        return
    
    print("Step 2: Logging in...")
    login_data = {"username": reg_data["username"], "password": reg_data["password"]}
    r = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if r.status_code != 200:
        print(f"Login failed: {r.text}")
        return
    
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Step 3: Creating project with format from screenshot...")
    # Based on user's screenshot
    proj_data = {
        "name": "软件",
        "description": "1",
        "course_name": "1",
        "start_date": "2026-05-07",
        "deadline": "2026-05-20T00:00:00" # ISO format which frontend likely sends
    }
    
    r = requests.post(f"{BASE_URL}/projects", json=proj_data, headers=headers)
    print(f"Status Code: {r.status_code}")
    print(f"Response Body: {r.text}")

if __name__ == "__main__":
    try:
        test_create()
    except Exception as e:
        print(f"Test script crashed: {e}")
