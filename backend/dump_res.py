import requests
import json
import logging

# Mute requests logs to not pollute output
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

URL = "http://localhost:5000/process-student"
payload = {
    "name": "Test Junior Merit",
    "income": 500000,
    "marks": 65,
    "category": "General",
    "course_fee": 5000,
    "course_level": "Plus 2",
    "state": "Odisha",
    "special_case": "none",
    "cibil_score": 0,
    "college_tier": "Unknown",
    "collateral_amount": 0
}

try:
    res = requests.post(URL, json=payload).json()
    with open("test_output.json", "w") as f:
        json.dump(res.get("scholarships", []), f, indent=2)
except Exception as e:
    with open("test_output.json", "w") as f:
        f.write(str(e))
