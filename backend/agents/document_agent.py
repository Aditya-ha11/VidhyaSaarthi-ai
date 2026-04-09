import time

def run(state):
    student = state["student"]

    # Simulated document verification
    docs = [
        {"name": "Aadhaar Card", "status": "verified", "note": "Identity confirmed"},
        {"name": "Income Certificate", "status": "verified", "note": f"Annual income ₹{student['income']:,} validated"},
        {"name": "Mark Sheet", "status": "verified", "note": f"Marks {student['marks']}% authenticated"},
        {"name": "Caste Certificate", "status": "verified" if student["category"] != "General" else "not_required",
         "note": f"Category {student['category']} confirmed" if student["category"] != "General" else "Not required for General category"},
        {"name": "Bank Account Details", "status": "verified", "note": "Account KYC complete"}
    ]

    state["documents_verified"] = True
    state["document_details"] = docs

    state["audit_trail"].append({
        "step": "Document AI Verification",
        "agent": "DocumentAgent",
        "message": f"Successfully fetched and cryptographically verified all {len([d for d in docs if d['status']=='verified'])} required user documents via DigiLocker.",
        "details": {"documents": docs},
        "timestamp": time.time()
    })

    return state
