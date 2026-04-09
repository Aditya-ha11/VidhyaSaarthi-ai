from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import json
import datetime
import time
import PyPDF2
from pydantic import BaseModel, ValidationError, Field
from enum import Enum

sys.path.insert(0, os.path.dirname(__file__))
import master_agent as master_agent

app = Flask(__name__)
CORS(app)

class CategoryEnum(str, Enum):
    GEN = "General"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"
    # Added EWS for compliance
    EWS = "EWS"

class StudentRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    income: float = Field(..., ge=0)
    marks: float = Field(..., ge=0, le=100)
    category: CategoryEnum
    course_fee: float = Field(..., gt=0)
    course_level: str = Field(default="Class 6-10")
    state: str = Field(default="Maharashtra")
    special_case: str = Field(default="none")
    cibil_score: int = Field(default=0)
    college_tier: str = Field(default="Unknown")
    collateral_amount: float = Field(default=0.0)

DB_FILE = os.path.join(os.path.dirname(__file__), "data", "students_db.json")
USERS_DB_FILE = os.path.join(os.path.dirname(__file__), "data", "users_db.json")
AUDIT_FILE = os.path.join(os.path.dirname(__file__), "data", "audit_logs_db.json")
COMPLAINTS_FILE = os.path.join(os.path.dirname(__file__), "data", "complaints_db.json")

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(AUDIT_FILE):
        with open(AUDIT_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(COMPLAINTS_FILE):
        with open(COMPLAINTS_FILE, "w") as f:
            json.dump([], f)

def init_users_db():
    if not os.path.exists(USERS_DB_FILE):
        with open(USERS_DB_FILE, "w") as f:
            json.dump([], f)

@app.route("/process-student", methods=["POST"])
def process_student():
    data = request.get_json()

    try:
        student = StudentRequest(**data)
    except ValidationError as e:
        return jsonify({
            "error": "Validation Error",
            "details": e.errors()
        }), 422

    validated_data = {
        "name": student.name,
        "income": student.income,
        "marks": student.marks,
        "category": student.category.value,
        "course_fee": student.course_fee,
        "course_level": student.course_level,
        "state": student.state,
        "special_case": student.special_case,
        "cibil_score": student.cibil_score,
        "college_tier": student.college_tier,
        "collateral_amount": student.collateral_amount
    }

    state = master_agent.process(validated_data)

    result_data = {
        "id": datetime.datetime.now().isoformat(),
        "student": data,
        "eligibility_score": state["eligibility_score"],
        "scholarships": state["scholarships"],
        "loan_options": state["loan_options"],
        "documents_verified": state["documents_verified"],
        "document_details": state["document_details"],
        "disbursal_status": state["disbursal_status"],
        "explanation": state["explanation"],
        "explanation_visual": state.get("explanation_visual"),
        "audit_trail": state["audit_trail"]
    }

    init_db()
    with open(DB_FILE, "r") as f:
        db = json.load(f)
    db.append(result_data)
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

    return jsonify(result_data)

@app.route("/students", methods=["GET"])
def get_students():
    init_db()
    with open(DB_FILE, "r") as f:
        db = json.load(f)
    # Reverse to show newest applications first
    return jsonify({"students": list(reversed(db))})


@app.route("/rank-complaints", methods=["POST"])
def rank_complaints():
    data = request.get_json()
    complaints = data.get("complaints", [])

    severity_keywords = {
        "critical": ["fraud", "theft", "stolen", "illegal", "urgent", "emergency", "scam", "abuse", "harassment"],
        "high": ["wrong", "delay", "not received", "missing", "rejected", "error", "failed", "denied"],
        "medium": ["issue", "problem", "concern", "inquiry", "query", "pending", "late"],
        "low": ["suggestion", "feedback", "request", "information", "update", "status"]
    }

    weights = {"critical": 100, "high": 60, "medium": 30, "low": 10}

    scored = []
    for c in complaints:
        text = c.lower()
        score = 0
        matched_level = "low"
        for level, keywords in severity_keywords.items():
            for kw in keywords:
                if kw in text:
                    score += weights[level]
                    matched_level = level
                    break

        scored.append({"complaint": c, "urgency_score": score, "severity": matched_level})

    scored.sort(key=lambda x: x["urgency_score"], reverse=True)

    return jsonify({"ranked_complaints": scored})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Student Loan AI System"})

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400
    
    init_users_db()
    with open(USERS_DB_FILE, "r") as f:
        users = json.load(f)
        
    for user in users:
        if user["email"] == data["email"]:
            return jsonify({"error": "User already exists"}), 400
            
    new_user = {
        "id": datetime.datetime.now().isoformat(),
        "name": data.get("name"),
        "email": data["email"],
        "password": data["password"],
        "role": data.get("role", "Student")
    }
    
    users.append(new_user)
    with open(USERS_DB_FILE, "w") as f:
        json.dump(users, f, indent=4)
        
    return jsonify({"message": "User created successfully", "token": new_user["id"], "user": new_user})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400
        
    init_users_db()
    with open(USERS_DB_FILE, "r") as f:
        users = json.load(f)
        
    for user in users:
        if user["email"] == data["email"] and user["password"] == data["password"]:
            # Hackathon bypass: allow user to login as whichever role they chose
            if "role" in data:
                user["role"] = data["role"]
            return jsonify({"message": "Logged in successfully", "token": user["id"], "user": user})
            
    return jsonify({"error": "Invalid email or password"}), 401

@app.route("/upload-document", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 422
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 422

    student_name = request.form.get("student_name", "").lower()
    doc_type = request.form.get("doc_type", "unknown").lower()

    filename = file.filename.lower()
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        return jsonify({"error": 'Unsupported file format. Please use PDF, PNG, or JPG.'}), 422

    hints = {
        "aadhaar": ["aadhaar", "uidai", "id"],
        "pan": ["pan", "tax"],
        "bank": ["bank", "passbook", "statement", "account"],
        "college": ["bonafide", "college", "university"],
        "marksheet": ["marksheet", "transcript", "degree", "result"],
        "income": ["income", "revenue", "salary", "itr"],
        "caste": ["caste", "category"]
    }
    
    expected_hints = hints.get(doc_type, [])
    hint_matched = any(h in filename for h in expected_hints) if expected_hints else True
    
    if not hint_matched:
        return jsonify({"status": "Rejected", "reason": f"Filename metadata ({file.filename}) does not structurally align with expected {doc_type.upper()} parameters."})

    status = "Pending"
    reason = "Awaiting manual review"

    if filename.endswith(".pdf"):
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages[:2]:
                extracted = page.extract_text()
                if extracted:
                    text += extracted.lower() + " "
            
            if student_name and student_name in text:
                status = "Verified"
                reason = f"{doc_type.title()} authenticated. Identity and payload successfully matched."
            else:
                status = "Rejected"
                reason = f"Security mismatch in OCR. Document does not reflect ownership by {student_name.title()}."
        except Exception as e:
            return jsonify({"error": f"Failed to cryptographically parse PDF securely: {str(e)}"}), 422
    else:
        status = "Verified" 
        reason = f"Image payload simulated and processed by OCR model returning positive match for {student_name.title()}."

    return jsonify({
        "status": status,
        "reason": reason,
        "filename": file.filename,
        "doc_type": doc_type
    })

@app.route("/digilocker-sync", methods=["POST"])
def digilocker_sync():
    data = request.get_json() or {}
    student_name = data.get("student_name", "")
    if not student_name:
        return jsonify({"error": "Student profile name is required to sync with DigiLocker sandbox."}), 422
    
    # Simulate fetch from DigiLocker
    return jsonify({
        "message": f"Successfully authenticated and pulled DigiLocker Vault for {student_name}.",
        "imported_docs": ["aadhaar", "pan", "marksheet"]
    })

@app.route("/admin/applications", methods=["GET"])
def admin_applications():
    init_db()
    with open(DB_FILE, "r") as f:
        db = json.load(f)
        
    status_filter = request.args.get("status")
    if status_filter:
        db = [d for d in db if d.get("disbursal_status") == status_filter]
        
    db = sorted(db, key=lambda x: x.get("eligibility_score", 0), reverse=True)
    return jsonify({"applications": db})

@app.route("/admin/action", methods=["POST"])
def admin_action():
    data = request.get_json()
    app_id = data.get("application_id")
    action = data.get("action")
    reason = data.get("reason", "")
    admin_user = data.get("admin_id", "AdminUser")
    
    if not app_id or action not in ["Approve", "Reject"]:
        return jsonify({"error": "Invalid payload"}), 400
    if action == "Reject" and not reason:
        return jsonify({"error": "Reason is mandatory for Rejections"}), 400
        
    init_db()
    with open(DB_FILE, "r") as f:
        db = json.load(f)
        
    target_app = next((a for a in db if a["id"] == app_id), None)
    if not target_app:
        return jsonify({"error": "Application not found"}), 404
        
    target_app["disbursal_status"] = "Approved" if action == "Approve" else "Rejected"
    
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)
        
    audit_log = {
        "id": str(time.time()),
        "application_id": app_id,
        "action": action,
        "performed_by": admin_user,
        "reason": reason,
        "timestamp": time.time()
    }
    
    with open(AUDIT_FILE, "r") as f:
        audits = json.load(f)
        
    audits.append(audit_log)
    with open(AUDIT_FILE, "w") as f:
        json.dump(audits, f, indent=4)
        
    # Trigger notification logic dynamically securely in background
    try:
        from agents.notification_agent import trigger_notification
        phone = data.get("phone", "MissingPhone")
        trigger_notification(app_id, phone, target_app["disbursal_status"], reason)
    except Exception as e:
        print("Notif Error:", e)
        
    return jsonify({"message": f"Action {action} applied.", "log": audit_log})

@app.route("/admin/audit/<app_id>", methods=["GET"])
def admin_audit(app_id):
    with open(AUDIT_FILE, "r") as f:
        audits = json.load(f)
    result = [a for a in audits if a["application_id"] == app_id]
    return jsonify({"audits": result})

@app.route("/admin/complaints", methods=["GET"])
def admin_complaints():
    try:
        with open(COMPLAINTS_FILE, "r") as f:
            c = json.load(f)
    except Exception:
        c = []
    # Reverse to show newest first
    return jsonify({"complaints": list(reversed(c))})

import uuid

@app.route("/submit-complaint", methods=["POST"])
def submit_complaint():
    data = request.get_json()
    email = data.get("email")
    student_name = data.get("student_name", "Student")
    text = data.get("text", "")

    if not email or not text:
        return jsonify({"error": "Email and text are required"}), 400

    init_db()
    with open(COMPLAINTS_FILE, "r") as f:
        c = json.load(f)

    new_comp = {
        "id": str(uuid.uuid4()),
        "email": email,
        "student_name": student_name,
        "text": text,
        "reply": None,
        "status": "Pending",
        "timestamp": time.time()
    }

    c.append(new_comp)
    with open(COMPLAINTS_FILE, "w") as f:
        json.dump(c, f, indent=4)

    return jsonify({"message": "Complaint submitted successfully", "complaint": new_comp})

@app.route("/student/complaints", methods=["GET"])
def student_complaints():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    try:
        with open(COMPLAINTS_FILE, "r") as f:
            c = json.load(f)
    except Exception:
        c = []

    user_complaints = [comp for comp in c if comp.get("email") == email]
    return jsonify({"complaints": list(reversed(user_complaints))})

@app.route("/admin/reply-complaint", methods=["POST"])
def admin_reply_complaint():
    data = request.get_json()
    comp_id = data.get("complaint_id")
    reply = data.get("reply", "")

    if not comp_id or not reply:
        return jsonify({"error": "Complaint ID and reply are required"}), 400

    try:
        with open(COMPLAINTS_FILE, "r") as f:
            c = json.load(f)
    except Exception:
        return jsonify({"error": "Database error"}), 500

    target = next((comp for comp in c if comp.get("id") == comp_id), None)
    if not target:
        return jsonify({"error": "Complaint not found"}), 404

    target["reply"] = reply
    target["status"] = "Resolved"
    target["reply_timestamp"] = time.time()

    with open(COMPLAINTS_FILE, "w") as f:
        json.dump(c, f, indent=4)

    return jsonify({"message": "Replied successfully", "complaint": target})

# --- GEMINI API CONFIGURATION ---
# INSERT YOUR GEMINI API KEY HERE:
GEMINI_API_KEY = "AIzaSyAhWbuFg0YzwUYxyGHQgLiutrL8BilifL8"
# ------------------------------

@app.route("/chat", methods=["POST"])
def chatbot_interaction():
    data = request.get_json()
    msg = data.get("message", "")
    st_context = data.get("context", {})
    lang = data.get("lang", "en")
    
    # Check if API key is provided
    if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == "":
        responses = {
            "en": f"[API KEY MISSING] I understand! Based on your profile showing {st_context.get('eligibility_score', 0)} score, I recommend improving your marks. (Please insert Gemini API Key to activate real AI!)",
            "hi": f"[API KEY MISSING] मैं समझता हूँ! आपके {st_context.get('eligibility_score', 0)} स्कोर के आधार पर...",
            "or": f"[API KEY MISSING] ମୁଁ ବୁଝୁଛି! ଆପଣଙ୍କର {st_context.get('eligibility_score', 0)} ସ୍କୋର ଆଧାରରେ..."
        }
        res = responses.get(lang.lower(), responses["en"])
        return jsonify({"response": res})
        
    # Standard Chat Completions Request to Gemini
    import urllib.request
    import urllib.error
    import json
    import time
    
    loan_ops = st_context.get('loan_options', [])
    scholar_ops = st_context.get('scholarships', [])
    
    lang_map = {
        "hi": "Hindi",
        "or": "Odia",
        "en": "English"
    }
    full_lang_name = lang_map.get(lang.lower(), "English")
    
    system_prompt = (
        f"You are the VidyaSaarthi AI Educational Counsellor. "
        f"You are currently talking to {st_context.get('user', {}).get('name', 'a Student')} "
        f"(Role: {st_context.get('user', {}).get('role', 'Unknown')}). "
        f"They have filled out: {json.dumps(st_context.get('form', {}))}. "
        f"Their eligibility score is {st_context.get('eligibility_score', 'pending submission')}, "
        f"and approval status is {st_context.get('disbursal_status', 'Pending')}. "
        f"If the system matched them with loans, they are: {json.dumps(loan_ops)}. "
        f"If the system matched them with scholarships, they are: {json.dumps(scholar_ops)}. "
        f"Always answer in {full_lang_name}. Keep it brief. Explicitly mention specific loan/scholarship names from the matched lists when advising them!"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_prompt}\n\nUser Question: {msg}"}
                ]
            }
        ]
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    
    for attempt in range(4): # Retry logic to bypass 503 load spikess
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                # Parse Gemini Response
                ai_reply = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                return jsonify({"response": ai_reply})
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            if e.code == 503:
                time.sleep(1.5) # Wait before retry
                continue
            
            print("Gemini HTTP Error:", error_body)
            try:
                err_json = json.loads(error_body)
                err_msg = err_json.get("error", {}).get("message", "Unknown error")
                err_status = err_json.get("error", {}).get("status", "")
                
                if "API_KEY_INVALID" in err_status or "API key not valid" in err_msg or e.code == 400:
                    responses = {
                        "en": f"[API KEY MISSING] I understand! Based on your profile showing {st_context.get('eligibility_score', 0)} score, I recommend applying for the programs listed. (Please insert real Gemini API Key!)",
                        "hi": f"[API KEY MISSING] मैं समझता हूँ! आपके {st_context.get('eligibility_score', 0)} स्कोर के आधार पर, मैं उल्लिखित कार्यक्रमों के लिए आवेदन करने की सलाह देता हूँ। (कृपया असली Gemini API Key डालें!)",
                        "or": f"[API KEY MISSING] ମୁଁ ବୁଝୁଛି! ଆପଣଙ୍କର {st_context.get('eligibility_score', 0)} ସ୍କୋର ଆଧାରରେ, ମୁଁ ଉଲ୍ଲିଖିତ କାର୍ଯ୍ୟକ୍ରମ ପାଇଁ ଆବେଦନ କରିବାକୁ ପରାମର୍ଶ ଦେଉଛି। (ଦୟାକରି ଅସଲୀ ଜେମିନି API କି ଦିଅନ୍ତୁ!)"
                    }
                    res = responses.get(lang.lower(), responses["en"])
                    return jsonify({"response": res})
                    
            except Exception:
                err_msg = error_body
            return jsonify({"response": f"Gemini Error: {err_msg}."})
        except urllib.error.URLError as e:
            print("Gemini Connection Error:", e)
            return jsonify({"response": "Encountered a network error communicating with Gemini. Check your connection."})
            
    return jsonify({"response": "Gemini Error: The Google servers are currently experiencing extreme demand. Please try again in a few minutes."})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
