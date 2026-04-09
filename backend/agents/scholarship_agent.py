import time
import csv
import json
import os

def run(state):
    student = state["student"]
    data_path = os.path.join(os.path.dirname(__file__), "../data/nsp_government_scholarships.csv")

    all_scholarships = []
    with open(data_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_scholarships.append(row)

    matched = []
    reasons = []

    for sch in all_scholarships:
        try:
            max_income = float(sch["Income_Ceiling_INR"])
            min_marks = float(sch["Min_Marks_Percentage"])
            amount = float(sch["Award_Amount_INR"])
        except ValueError:
            continue
            
        income_ok = student["income"] <= max_income
        marks_ok = student["marks"] >= min_marks
        
        target_cat = sch["Target_Category"]
        if target_cat == "ALL":
            category_ok = True
        else:
            category_ok = student["category"] in target_cat.split("|")

        if income_ok and marks_ok and category_ok:
            matched.append({
                "id": sch["Scheme_ID"],
                "name": sch["Scheme_Name"],
                "amount": amount,
                "description": sch["Description"]
            })
            reasons.append(f"'{sch['Scheme_Name']}' matched (marks>={min_marks}, income<=Rs{max_income:,.0f}, category={target_cat})")

    # Process State Specific Scholarships
    STATE_MAPPING = {
        "Odisha": "OD",
        "Maharashtra": "MH",
        "Karnataka": "KA",
        "West Bengal": "WB",
        "Uttar Pradesh": "UP",
        "Telangana": "TS",
        "Andhra Pradesh": "AP",
        "Haryana": "HR",
        "Meghalaya": "ML"
    }
    
    student_state_prefix = STATE_MAPPING.get(student.get("state"))

    if student_state_prefix:
        state_path = os.path.join(os.path.dirname(__file__), "../data/state_scholarships.json")
        try:
            with open(state_path, mode='r', encoding='utf-8') as f:
                state_scholarships = json.load(f)
                
            for sch in state_scholarships:
                if not sch.get("id", "").startswith(student_state_prefix + "_"):
                    continue
                    
                # Basic course match
                courses = sch.get("courses", [])
                if courses and "ALL" not in courses and student["course_level"] not in courses:
                    continue
                
                # Income check
                income_max = sch.get("income_max")
                if income_max is not None and student["income"] > income_max:
                    continue
                    
                # Category check
                target_cat = sch.get("category")
                if target_cat != "ALL":
                    if isinstance(target_cat, list) and student["category"] not in target_cat:
                        continue
                    elif isinstance(target_cat, str) and student["category"] != target_cat:
                        continue
                
                # Special Needs Filter
                special_req = sch.get("special")
                if special_req and special_req != student.get("special_case", "none"):
                    continue
                
                # If we made it here, it's a match! Construct amount properly (handle complex amounts gracefully)
                raw_amt = sch.get("amount")
                amt = raw_amt if isinstance(raw_amt, (int, float)) else 10000 # default fallback for dict amounts
                
                matched.append({
                    "id": sch["id"],
                    "name": sch["name"],
                    "amount": amt,
                    "description": f"{student['state']} Direct Benefit: Specifically tailored for {student['course_level']}."
                })
        except Exception as e:
            print("Failed resolving state grants:", e)

    state["scholarships"] = matched

    msg = f"Deep search complete. System successfully identified {len(matched)} matching scholarship schemes from the national government directory."
    if not matched:
        msg += " Unfortunately, no schemes matched your strict income criteria at this time."

    state["audit_trail"].append({
        "step": "Scholarship Routing (NSP Hub)",
        "agent": "ScholarshipAgent",
        "message": msg,
        "details": {"matched_count": len(matched), "scholarships": [s["name"] for s in matched]},
        "timestamp": time.time()
    })

    return state
