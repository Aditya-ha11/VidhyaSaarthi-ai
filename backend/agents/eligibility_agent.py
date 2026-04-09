import time

def run(state):
    student = state["student"]
    marks = student["marks"]
    income = student["income"]

    # 40% from marks (marks/100 * 40)
    marks_score = (marks / 100) * 40

    # Income component: lower income → higher score (up to 60 points)
    # income=0 → 60pts, income=1200000+ → 0pts
    max_income_threshold = 1200000
    income_clamped = min(income, max_income_threshold)
    income_score = ((max_income_threshold - income_clamped) / max_income_threshold) * 60

    raw_score = marks_score + income_score
    eligibility_score = min(round(raw_score, 2), 100)

    # Soft-Approval Bands Logic
    reason_codes = []
    if eligibility_score > 65:
        decision_zone = "AUTO_APPROVED"
        disbursal_status = "Approved"
    elif 55 <= eligibility_score <= 65:
        decision_zone = "MANUAL_REVIEW"
        disbursal_status = "Under Review"
    else:
        decision_zone = "DENIED"
        disbursal_status = "Rejected"

    if decision_zone in ["MANUAL_REVIEW", "DENIED"]:
        if marks < 60:
            reason_codes.append("MARKS_BELOW_THRESHOLD")
        if income > 800000:
            reason_codes.append("INCOME_TOO_HIGH")
        if student.get("course_level") == "Unknown":
            reason_codes.append("COURSE_NOT_ELIGIBLE")

    state["eligibility_score"] = eligibility_score
    state["decision_zone"] = decision_zone
    state["reason_codes"] = reason_codes
    state["disbursal_status"] = disbursal_status
    state["eligibility_details"] = {
        "marks_score": round(marks_score, 2),
        "income_score": round(income_score, 2)
    }

    state["audit_trail"].append({
        "step": "Eligibility Verification",
        "agent": "EligibilityAgent",
        "message": f"Successfully calculated eligibility score of {eligibility_score:.1f}/100. Categorized as {decision_zone}.",
        "details": {
            "marks_score": round(marks_score, 2),
            "income_score": round(income_score, 2),
            "total_score": eligibility_score,
            "decision_zone": decision_zone,
            "reason_codes": reason_codes
        },
        "timestamp": time.time()
    })

    return state
