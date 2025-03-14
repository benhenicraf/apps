import frappe
import requests
import json

@frappe.whitelist(allow_guest=True)
def get_notifications():
    """Fetch notifications from Wialon API"""
    
    # Get session ID from components_core
    session_id = frappe.db.get_single_value("Wialon API Configuration", "session_id")
    if not session_id:
        return {"error": "No active session"}

    WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"
    params = {
        "svc": "resource/get_notification_data",
        "params": json.dumps({
            "itemId": 0,  # 0 = fetch all notifications
            "col": []  # Empty = fetch latest notifications
        }),
        "sid": session_id
    }

    response = requests.post(WIALON_API_URL, data=params)
    if response.status_code != 200:
        return {"error": "Failed to fetch notifications"}

    return response.json()
