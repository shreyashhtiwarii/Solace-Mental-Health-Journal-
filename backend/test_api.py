import urllib.request
import urllib.error
import json
import uuid

def test_api():
    base = "http://127.0.0.1:8000"
    uname = f"test_{uuid.uuid4().hex[:6]}"
    
    print("--- Testing /register ---")
    req = urllib.request.Request(
        f"{base}/register",
        data=json.dumps({"username": uname, "password": "password"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        res = urllib.request.urlopen(req)
        print("Register Success:", res.read().decode())
    except urllib.error.HTTPError as e:
        print("Register Error:", e.code, e.read().decode())
    except Exception as e:
        print("Register Exception:", str(e))
        
    print("\n--- Testing /login ---")
    data = urllib.parse.urlencode({"username": uname, "password": "password"}).encode()
    req = urllib.request.Request(
        f"{base}/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        res = urllib.request.urlopen(req)
        print("Login Success:", res.read().decode())
    except urllib.error.HTTPError as e:
        print("Login Error:", e.code, e.read().decode())
    except Exception as e:
        print("Login Exception:", str(e))

test_api()
