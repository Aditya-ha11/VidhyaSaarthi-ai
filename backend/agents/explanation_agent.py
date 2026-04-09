import time

def run(state):
    student = state["student"]
    score = state["eligibility_score"]
    scholarships = state["scholarships"]
    loans = state["loan_options"]
    status = state["disbursal_status"]

    parts = []

    # Academic strength
    if student["marks"] >= 85:
        parts.append(f"Strong academic profile with {student['marks']}% marks (top tier).")
    elif student["marks"] >= 70:
        parts.append(f"Good academic standing with {student['marks']}% marks.")
    elif student["marks"] >= 50:
        parts.append(f"Moderate academic performance with {student['marks']}% marks.")
    else:
        parts.append(f"Academic performance ({student['marks']}%) is below average — improvement needed.")

    # Income level
    if student["income"] <= 200000:
        parts.append(f"Very low annual family income (₹{student['income']:,}) provides maximum income-based score benefit.")
    elif student["income"] <= 500000:
        parts.append(f"Low-to-middle income bracket (₹{student['income']:,}) provides good income-based support.")
    elif student["income"] <= 800000:
        parts.append(f"Middle income (₹{student['income']:,}) qualifies for partial income-based support.")
    else:
        parts.append(f"Higher family income (₹{student['income']:,}) limits income-based score contribution.")

    # Score summary
    parts.append(f"Combined eligibility score: {score:.1f}/100.")

    # Scholarships
    if scholarships:
        names = ", ".join([s["name"] for s in scholarships])
        total = sum(s["amount"] for s in scholarships)
        parts.append(f"Qualified for {len(scholarships)} scholarship(s): {names} (total ₹{total:,}).")
    else:
        parts.append("No scholarships matched the criteria (marks, income, and category must all qualify).")

    # Loan
    if loans:
        parts.append(f"{len(loans)} loan option(s) available from providers including {loans[0]['provider']} at {loans[0]['interest_rate']}% p.a.")
    else:
        parts.append("No loan options available — income exceeds all lender thresholds.")

    # Final decision & Suggestions
    decision_zone = state.get("decision_zone", "DENIED")
    reason_codes = state.get("reason_codes", [])
    
    if decision_zone == "AUTO_APPROVED":
        parts.append(f"APPROVED: You scored in the top tier ({score:.1f}). No manual review required.")
    elif decision_zone == "MANUAL_REVIEW":
        parts.append(f"UNDER REVIEW: Score ({score:.1f}) is in the conditional band. Awaiting human underwriter review.")
    else:
        parts.append(f"REJECTED: Profile doesn't meet minimum financing thresholds at this time.")

    suggestions = []
    if reason_codes:
        if "MARKS_BELOW_THRESHOLD" in reason_codes:
            gap = 60 - student["marks"]
            suggestions.append(f"Try to increase your academic marks by at least {gap}% to secure better options.")
        if "INCOME_TOO_HIGH" in reason_codes:
            suggestions.append(f"Your reported family income exceeds standard subsidy tiers. Provide valid income proof or consider private loans.")
        if "COURSE_NOT_ELIGIBLE" in reason_codes:
            suggestions.append(f"The selected course level may not be eligible for primary scholarships. Consider enrolling in an accredited STEM or formal degree program.")
            
    state["improvement_suggestions"] = suggestions
    if suggestions:
        parts.append("\nAI Suggestions: " + " ".join(suggestions))

    explanation = " ".join(parts)
    state["explanation"] = explanation

    # Create structured visual explanation data
    details = state.get("eligibility_details", {"marks_score": 0, "income_score": 0})
    explanation_visual = {
        "factors": [
            {
                "label": "Academic Performance",
                "value": f"{student['marks']}%",
                "score": details["marks_score"],
                "max": 40,
                "color": "var(--primary)",
                "icon": "📚",
                "message": f"Contributes {details['marks_score']} / 40 points"
            },
            {
                "label": "Income Bracket",
                "value": f"₹{student['income']:,}",
                "score": details["income_score"],
                "max": 60,
                "color": "var(--success)",
                "icon": "⚖️",
                "message": f"Contributes {details['income_score']} / 60 points"
            }
        ],
        "scholarships_match": len(scholarships),
        "loans_match": len(loans),
        "decision": status
    }
    state["explanation_visual"] = explanation_visual

    state["audit_trail"].append({
        "step": "Explanation Agent",
        "agent": "ExplanationAgent",
        "message": "Rule-based explanation generated covering academic strength, income level, scholarships, loans, and final decision",
        "details": {"explanation": explanation},
        "timestamp": time.time()
    })

    return state
