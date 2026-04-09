import time
import json
import os

def run(state):
    student = state["student"]
    scholarships = state.get("scholarships", [])
    
    # Calculate total funds already covered by scholarships
    total_awarded = sum(s["amount"] for s in scholarships)
    
    # The actual financing gap
    financing_gap = student["course_fee"] - total_awarded
    
    data_path = os.path.join(os.path.dirname(__file__), "../data/loan_logic.json")
    with open(data_path, mode='r', encoding='utf-8') as f:
        logic = json.load(f)

    matched_loans = []
    msg_details = ""
    flags = []
    
    if financing_gap <= 0:
        msg_details = "Funding requirements securely met through allocated scholarships. No external bank loans are necessary."
        state["loan_options"] = []
    else:
        # Starting Score
        tot_score = 0
        
        # 1. College Tier
        ct = student.get("college_tier", "Unknown")
        tot_score += logic["college_tier"].get(ct, 0)
        
        # 2. Academics
        marks = student["marks"]
        if marks >= logic["academics"]["high"]["min"]:
            tot_score += logic["academics"]["high"]["score"]
        elif marks >= logic["academics"]["medium"]["min"]:
            tot_score += logic["academics"]["medium"]["score"]
        else:
            tot_score += logic["academics"]["low"]["score"]
            flags.append(logic["academics"]["low"]["reason"])
            
        # 3. Income
        inc = student["income"]
        if inc >= logic["income"]["high"]["min"]:
            tot_score += logic["income"]["high"]["score"]
        elif inc >= logic["income"]["medium"]["min"]:
            tot_score += logic["income"]["medium"]["score"]
        else:
            tot_score += logic["income"]["low"]["score"]
            flags.append(logic["income"]["low"]["reason"])
            
        # 4. CIBIL
        cib = student.get("cibil_score", 0)
        if cib >= logic["cibil"]["excellent"]["min"]:
            tot_score += logic["cibil"]["excellent"]["score"]
        elif cib >= logic["cibil"]["good"]["min"]:
            tot_score += logic["cibil"]["good"]["score"]
        elif cib >= logic["cibil"]["average"]["min"]:
            tot_score += logic["cibil"]["average"]["score"]
        else:
            tot_score += logic["cibil"]["poor"]["score"]
            flags.append(logic["cibil"]["poor"]["reason"])
            
        # 5. Loan Collateral
        collat = student.get("collateral_amount", 0)
        if financing_gap <= logic["loan_collateral"]["low_loan"]["max"]:
            tot_score += logic["loan_collateral"]["low_loan"]["score"]
        elif financing_gap <= logic["loan_collateral"]["medium_loan"]["max"]:
            tot_score += logic["loan_collateral"]["medium_loan"]["score"]
        else:
            if collat >= financing_gap:
                tot_score += logic["loan_collateral"]["high_loan"]["with_full_collateral"]
            elif collat > 0:
                tot_score += logic["loan_collateral"]["high_loan"]["with_partial_collateral"]["score"]
                flags.append(logic["loan_collateral"]["high_loan"]["with_partial_collateral"]["reason"])
            else:
                tot_score += logic["loan_collateral"]["high_loan"]["no_collateral"]["score"]
                flags.append(logic["loan_collateral"]["high_loan"]["no_collateral"]["reason"])
                
        # 6. Course ROI
        course = student.get("course_level", "").lower()
        if any(c.lower() in course for c in logic["course_roi"]["high"]["courses"]):
            tot_score += logic["course_roi"]["high"]["score"]
        elif any(c.lower() in course for c in logic["course_roi"]["medium"]["courses"] + ["bachelor", "plus", "diploma"]):
            tot_score += logic["course_roi"]["medium"]["score"]
        else:
            tot_score += logic["course_roi"]["low"]["score"]
            flags.append(logic["course_roi"]["low"]["reason"])

        # Decide Action
        status = "Rejected"
        lender_tier = None
        if tot_score >= logic["decision_thresholds"]["approved"]:
            status = "Approved"
            lender_tier = "high"
        elif tot_score >= logic["decision_thresholds"]["conditional"]:
            status = "Conditional"
            lender_tier = "medium"
        else:
            status = "Rejected"
            lender_tier = "low"
            
        # Fetch Lenders
        lenders = logic["lenders"].get(lender_tier, [])
        for i, ldr in enumerate(lenders):
            cap = financing_gap
            r = ldr["interest"] / 1200
            n = 20 * 12
            emi = (cap * r * ((1 + r)**n)) / (((1 + r)**n) - 1) if r > 0 else cap / n
            
            monthly_income = student["income"] / 12 if student["income"] > 0 else 0
            dti_ratio = (emi / monthly_income * 100) if monthly_income > 0 else 100
            
            affordability_flag = "AFFORDABILITY_RISK" if dti_ratio > 30 else "SAFE"
            
            matched_loans.append({
                "id": f"LOAN_{lender_tier.upper()}_{i}",
                "provider": ldr["bank"],
                "scheme_name": f"{ldr['type']} Education Loan",
                "amount": cap,
                "interest_rate": ldr["interest"],
                "tenure_years": 20,
                "description": f"Loan decision: {status} (Score: {tot_score}). Identified risks: {', '.join(flags) if flags else 'None'}.",
                "emi_estimate": round(emi, 2),
                "affordability_flag": affordability_flag,
                "ratio_percentage": round(dti_ratio, 2)
            })
            
        msg_details = f"Underwriting processing complete. Final Score: {tot_score}/100. Status: {status}. Risks: {len(flags)}. Financing Gap: ₹{financing_gap:,.2f}"
            
        state["loan_options"] = matched_loans
        
    state["audit_trail"].append({
        "step": "Bank Loan Assessment",
        "agent": "LoanAgent",
        "message": msg_details,
        "details": {
            "course_fee": student["course_fee"],
            "scholarships_awarded": total_awarded,
            "financing_gap": financing_gap,
            "providers": [l["provider"] for l in matched_loans]
        },
        "timestamp": time.time()
    })

    return state
