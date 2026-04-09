import time

def run(state):
    score = state["eligibility_score"]
    docs_ok = state["documents_verified"]

    if score > 60 and docs_ok:
        status = "Approved"
        reason = f"Score {score:.1f} > 60 AND documents verified → Approved for disbursal"
    else:
        status = "Pending"
        reasons = []
        if score <= 60:
            reasons.append(f"eligibility score {score:.1f} ≤ 60")
        if not docs_ok:
            reasons.append("document verification incomplete")
        reason = "Pending manual review: " + "; ".join(reasons)

    state["disbursal_status"] = status

    state["audit_trail"].append({
        "step": "Disbursal Agent",
        "agent": "DisbursalAgent",
        "message": f"Decision: {status} | {reason}",
        "details": {
            "score": score,
            "docs_verified": docs_ok,
            "status": status,
            "reason": reason
        },
        "timestamp": time.time()
    })

    return state
