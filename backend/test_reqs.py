import requests
import json

URL = "http://localhost:5000/process-student"

test_cases = [
    {
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
    },
    {
        "name": "Test Banishree",
        "income": 1000000,
        "marks": 40,
        "category": "General",
        "course_fee": 10000,
        "course_level": "BSc, BBA, BCA, Journalism",
        "state": "Odisha",
        "special_case": "disability",
        "cibil_score": 0,
        "college_tier": "Unknown",
        "collateral_amount": 0
    },
    {
        "name": "Test Math Talent",
        "income": 900000,
        "marks": 80,
        "category": "General",
        "course_fee": 5000,
        "course_level": "Plus 2",
        "state": "Odisha",
        "special_case": "math_talent",
        "cibil_score": 0,
        "college_tier": "Unknown",
        "collateral_amount": 0
    }
]

for i, tc in enumerate(test_cases):
    print(f"\n--- Running {tc['name']} ---")
    res = requests.post(URL, json=tc)
    data = res.json()
    if 'scholarships' in data:
        print("Matched Scholarships:")
        for sch in data['scholarships']:
            print(f"- {sch['name']} (₹{sch['amount']})")
    else:
        print("Error/No scholarships:", data)
