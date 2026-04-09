import time
import threading

def _send_notification(user_id, phone, message, platform="MSG91", lang="EN"):
    # Simulate API call to MSG91 or Twilio
    time.sleep(1)
    # Log the notification output
    print(f"\n[NOTIFICATION AGENT | {platform}]: Sent to {phone or user_id} ({lang}) -> {message}\n")

def trigger_notification(user_id: str, phone: str, status: str, details: str = "", lang: str = "EN"):
    """
    Triggers an asynchronous notification.
    """
    templates = {
        "EN": {
            "Approved": "Your application has been approved. {}",
            "Rejected": "Your application has been rejected. {}",
            "Under Review": "Your application is under manual review. {}"
        },
        "HI": {
            "Approved": "आपका आवेदन स्वीकृत हो गया है। {}",
            "Rejected": "आपका आवेदन अस्वीकृत कर दिया गया है। {}",
            "Under Review": "आपका आवेदन मैन्युअल समीक्षा के अधीन है। {}"
        }
    }
    
    template_lang = lang if lang in templates else "EN"
    base_message = templates[template_lang].get(status, f"Application status updated to: {status}. {{}}")
    message = base_message.format(details)

    # Fire and forget thread
    threading.Thread(target=_send_notification, args=(user_id, phone, message, "Twilio/MSG91", template_lang), daemon=True).start()
