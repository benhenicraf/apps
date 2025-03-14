import frappe
import requests
import json
from datetime import datetime, timedelta
from components_core.api.wialon_auth import get_valid_session

WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

FREQUENTLY_USED_EVENT_CODES = [1001, 1002, 1003, 1004, 1005]  # Start, stop, geofence entry/exit, speed violation

def ensure_wialon_unit(unit_id, unit_name="Unknown", unit_type="Vehicle"):
    """Create or update a Wialon Unit record."""
    existing = frappe.get_all("Wialon Unit", filters={"unit_id": unit_id})
    if not existing:
        doc = frappe.get_doc({
            "doctype": "Wialon Unit",
            "unit_id": unit_id,
            "name": unit_name,
            "type": unit_type,
            "last_updated": datetime.now()
        })
        doc.insert(ignore_permissions=True)
        frappe.log("Created Wialon Unit: {}".format(unit_id))
        print(f"Created Wialon Unit: {unit_id}")
    else:
        frappe.db.set_value("Wialon Unit", existing[0].name, "last_updated", datetime.now())
        frappe.log("Updated Wialon Unit: {}".format(unit_id))
        print(f"Updated Wialon Unit: {unit_id}")

@frappe.whitelist()
def fetch_notifications(time_from, time_to, event_codes=None):
    """Fetch notification events from Wialon for a given time range, optionally filtering by event codes."""
    config = frappe.get_single("Wialon API Configuration")
    if not config.resource_id:
        frappe.throw("Resource ID not configured in Wialon API Configuration")

    session_id = get_valid_session()
    
    params = {
        "resourceId": int(config.resource_id),
        "timeFrom": int(time_from),
        "timeTo": int(time_to),
        "type": "avl_evnt"
    }
    
    if event_codes:
        params["eventCode"] = event_codes
    
    try:
        response = requests.get(
            WIALON_API_URL,
            params={"svc": "events/get", "sid": session_id, "params": json.dumps(params)}
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            frappe.log_error(f"Wialon API Error: {data['error']}", "Wialon Notification Fetch")
            print(f"Wialon API Error in fetch_notifications: {data['error']}")
            return []
        frappe.log("Fetched notifications: {}".format(len(data.get("events", []))))
        print(f"Fetched {len(data.get('events', []))} notifications")
        return data.get("events", [])
    except Exception as e:
        frappe.log_error(f"Failed to fetch notifications: {str(e)}", "Wialon Notification Fetch")
        print(f"Failed to fetch notifications: {str(e)}")
        return []

@frappe.whitelist()
def fetch_messages(time_from, time_to, direction=None):
    """Fetch message events from Wialon for a given time range, optionally filtering by direction."""
    config = frappe.get_single("Wialon API Configuration")
    if not config.resource_id:
        frappe.throw("Resource ID not configured in Wialon API Configuration")

    session_id = get_valid_session()
    print(f"Session ID: {session_id}")
    frappe.log(f"Session ID: {session_id}")

    # Use core/search_items to fetch units and their messages
    params = {
        "spec": {
            "itemsType": "avl_unit",
            "propName": "sys_id",
            "propValueMask": str(config.resource_id),
            "sortType": "sys_id"
        },
        "force": 1,
        "flags": 0x0001 | 0x0400,  # Basic properties + messages
        "from": int(time_from),
        "to": int(time_to)
    }
    
    if direction:
        params["direction"] = direction
    
    print(f"Fetching messages with params: {json.dumps(params, indent=2)}")
    frappe.log(f"Fetching messages with params: {json.dumps(params)}")
    
    try:
        response = requests.get(
            WIALON_API_URL,
            params={"svc": "core/search_items", "sid": session_id, "params": json.dumps(params)}
        )
        response.raise_for_status()
        data = response.json()
        print(f"Raw API response: {json.dumps(data, indent=2)}")
        frappe.log(f"Raw API response: {json.dumps(data)}")
        
        if "error" in data:
            frappe.log_error(f"Wialon API Error: {data['error']}", "Wialon Message Fetch")
            print(f"Wialon API Error in fetch_messages: {data['error']}")
            return []
        
        # Extract messages from units
        messages = []
        units = data.get("items", [])
        for unit in units:
            unit_messages = unit.get("msgs", {}).get("data", [])
            for msg in unit_messages:
                messages.append({
                    "id": msg.get("i", 0),
                    "time": msg.get("t", 0),
                    "resourceId": unit.get("id", config.resource_id),
                    "details": msg,
                    "direction": "Incoming" if msg.get("f", 0) & 0x0001 else "Outgoing"
                })
        
        print(f"Fetched {len(messages)} messages")
        frappe.log(f"Fetched {len(messages)} messages")
        if messages:
            print("Sample message:", json.dumps(messages[0], indent=2))
        return messages
    except Exception as e:
        frappe.log_error(f"Failed to fetch messages: {str(e)}", "Wialon Message Fetch")
        print(f"Failed to fetch messages: {str(e)}")
        return []

def process_notifications(notifications):
    """Process and save notification events to the Wialon Notification DocType."""
    print(f"Processing {len(notifications)} notifications")
    frappe.log(f"Processing {len(notifications)} notifications")
    for event in notifications:
        event_time = datetime.fromtimestamp(event["time"])
        unit_id = str(event["resourceId"])
        event_type = get_event_type(event["eventCode"])
        message = json.dumps(event["details"])
        
        ensure_wialon_unit(unit_id)
        
        existing = frappe.get_all("Wialon Notification", filters={
            "template_id": event["id"],
            "unit_id": unit_id,
            "event_time": event_time
        })
        if not existing:
            doc = frappe.get_doc({
                "doctype": "Wialon Notification",
                "template_id": event["id"],
                "unit_id": unit_id,
                "event_time": event_time,
                "type": event_type,
                "message": message
            })
            doc.insert(ignore_permissions=True)
            print(f"Saved notification: {event['id']}")
            frappe.log(f"Saved notification: {event['id']}")
        else:
            print(f"Notification {event['id']} already exists, skipping")
            frappe.log(f"Notification {event['id']} already exists, skipping")

def get_event_type(event_code):
    """Map event code to human-readable type."""
    mapping = {
        1001: "Start of movement",
        1002: "Stop of movement",
        1003: "Geofence entry",
        1004: "Geofence exit",
        1005: "Speed limit exceeded",
    }
    return mapping.get(event_code, f"Unknown ({event_code})")

def trigger_workflow(notification_type, unit_id):
    """Trigger automated actions based on notification type."""
    if notification_type == "Speed limit exceeded":
        frappe.sendmail(
            recipients=["manager@example.com"],
            subject="Speed Violation Alert",
            message=f"Unit {unit_id} has violated speed limits."
        )
    elif notification_type == "Maintenance due":
        frappe.db.set_value("Unit", unit_id, "next_maintenance", datetime.now() + timedelta(days=90))

def process_messages(messages):
    """Process and save message events to the Wialon Message DocType."""
    print(f"Processing {len(messages)} messages")
    frappe.log(f"Processing {len(messages)} messages")
    for msg in messages:
        try:
            message_time = datetime.fromtimestamp(msg["time"])
            unit_id = str(msg["resourceId"])
            direction = msg.get("direction", "Unknown")
            content = json.dumps(msg["details"])
            
            ensure_wialon_unit(unit_id)
            
            existing = frappe.get_all("Wialon Message", filters={
                "message_id": msg["id"],
                "unit_id": unit_id,
                "message_time": message_time
            })
            if not existing:
                doc = frappe.get_doc({
                    "doctype": "Wialon Message",
                    "message_id": msg["id"],
                    "unit_id": unit_id,
                    "message_time": message_time,
                    "direction": direction,
                    "content": content
                })
                doc.insert(ignore_permissions=True)
                print(f"Saved message: {msg['id']}")
                frappe.log(f"Saved message: {msg['id']}")
            else:
                print(f"Message {msg['id']} already exists, skipping")
                frappe.log(f"Message {msg['id']} already exists, skipping")
        except Exception as e:
            print(f"Failed to process message {msg.get('id', 'unknown')}: {str(e)}")
            frappe.log_error(f"Failed to process message {msg.get('id', 'unknown')}: {str(e)}", "Wialon Message Process")

@frappe.whitelist()
def fetch_and_save_notifications():
    """Fetch and save notifications for the last 15 minutes, focusing on frequently used types."""
    now = datetime.now()
    time_to = int(now.timestamp())
    time_from = int((now - timedelta(minutes=15)).timestamp())
    
    notifications = fetch_notifications(time_from, time_to, event_codes=FREQUENTLY_USED_EVENT_CODES)
    process_notifications(notifications)

@frappe.whitelist()
def fetch_all_past_notifications():
    """Fetch and save all past notifications from the beginning to now, all types."""
    now = datetime.now()
    time_to = int(now.timestamp())
    time_from = 0  # Unix epoch
    
    notifications = fetch_notifications(time_from, time_to)
    process_notifications(notifications)

@frappe.whitelist()
def fetch_and_save_messages():
    """Fetch and save messages for the last 15 minutes."""
    now = datetime.now()
    time_to = int(now.timestamp())
    time_from = int((now - timedelta(minutes=15)).timestamp())
    
    messages = fetch_messages(time_from, time_to)
    process_messages(messages)

@frappe.whitelist()
def fetch_all_past_messages():
    """Fetch and save all past messages from the beginning to now."""
    now = datetime.now()
    time_to = int(now.timestamp())
    time_from = 0  # Unix epoch
    
    messages = fetch_messages(time_from, time_to)
    process_messages(messages)








# import frappe
# import requests
# import json
# from datetime import datetime, timedelta
# from components_core.api.wialon_auth import get_valid_session

# WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

# # Added list of frequently used event codes for filtering
# FREQUENTLY_USED_EVENT_CODES = [1001, 1002, 1003, 1004, 1005]  # Start, stop, geofence entry/exit, speed violation

# @frappe.whitelist()
# def fetch_notifications(time_from, time_to, event_codes=None):
#     """Fetch notification events from Wialon for a given time range, optionally filtering by event codes."""
#     config = frappe.get_single("Wialon API Configuration")
#     if not config.resource_id:
#         frappe.throw("Resource ID not configured in Wialon API Configuration")

#     session_id = get_valid_session()
    
#     params = {
#         "resourceId": int(config.resource_id),
#         "timeFrom": int(time_from),
#         "timeTo": int(time_to),
#         "type": "avl_evnt"
#     }
    
#     if event_codes:
#         params["eventCode"] = event_codes
    
#     try:
#         response = requests.get(
#             WIALON_API_URL,
#             params={"svc": "events/get", "sid": session_id, "params": json.dumps(params)}
#         )
#         response.raise_for_status()
#         data = response.json()
#         if "error" in data:
#             frappe.log_error(f"Wialon API Error: {data['error']}", "Wialon Notification Fetch")
#             return []
#         return data.get("events", [])  # Assuming the response has a list of events
#     except Exception as e:
#         frappe.log_error(f"Failed to fetch notifications: {str(e)}", "Wialon Notification Fetch")
#         return []

# def process_notifications(notifications):
#     """Process and save notification events to the Wialon Notification DocType."""
#     for event in notifications:
#         event_time = datetime.fromtimestamp(event["time"])
#         unit_id = event["resourceId"]
#         event_type = get_event_type(event["eventCode"])
#         message = json.dumps(event["details"])
        
#         existing = frappe.get_all("Wialon Notification", filters={
#             "template_id": event["id"],
#             "unit_id": unit_id,
#             "event_time": event_time
#         })
#         if not existing:
#             doc = frappe.get_doc({
#                 "doctype": "Wialon Notification",
#                 "template_id": event["id"],
#                 "unit_id": unit_id,
#                 "event_time": event_time,
#                 "type": event_type,
#                 "message": message
#             })
#             doc.insert(ignore_permissions=True)
#             trigger_workflow(event_type, unit_id)

# def get_event_type(event_code):
#     """Map event code to human-readable type."""
#     mapping = {
#         1001: "Start of movement",
#         1002: "Stop of movement",
#         1003: "Geofence entry",
#         1004: "Geofence exit",
#         1005: "Speed limit exceeded",
#         # Add more mappings as needed
#     }
#     return mapping.get(event_code, f"Unknown ({event_code})")

# def trigger_workflow(notification_type, unit_id):
#     """Trigger automated actions based on notification type."""
#     if notification_type == "Speed limit exceeded":
#         frappe.sendmail(
#             recipients=["manager@example.com"],
#             subject="Speed Violation Alert",
#             message=f"Unit {unit_id} has violated speed limits."
#         )
#     elif notification_type == "Maintenance due":
#         frappe.db.set_value("Unit", unit_id, "next_maintenance", datetime.now() + timedelta(days=90))

# @frappe.whitelist()
# def predict_maintenance(unit_id):
#     """Predict next maintenance date based on historical notifications."""
#     maintenance_notifs = frappe.get_all("Wialon Notification", filters={
#         "unit_id": unit_id,
#         "type": "Maintenance due"
#     }, fields=["event_time"], order_by="event_time desc")
    
#     if len(maintenance_notifs) < 2:
#         return "Insufficient data"
    
#     intervals = []
#     for i in range(len(maintenance_notifs) - 1):
#         interval = (maintenance_notifs[i]["event_time"] - maintenance_notifs[i+1]["event_time"]).days
#         intervals.append(interval)
    
#     avg_interval = sum(intervals) / len(intervals)
#     last_maintenance = maintenance_notifs[0]["event_time"]
#     next_maintenance = last_maintenance + timedelta(days=avg_interval)
#     return next_maintenance.strftime("%Y-%m-%d")

# @frappe.whitelist()
# def fetch_and_save_notifications():
#     """Fetch and save notifications for the last 15 minutes, focusing on frequently used types."""
#     now = datetime.now()
#     time_to = int(now.timestamp())
#     time_from = int((now - timedelta(minutes=15)).timestamp())
    
#     notifications = fetch_notifications(time_from, time_to, event_codes=FREQUENTLY_USED_EVENT_CODES)
#     process_notifications(notifications)

# @frappe.whitelist()
# def fetch_all_past_notifications():
#     """Fetch and save all past notifications from the beginning to now, all types."""
#     now = datetime.now()
#     time_to = int(now.timestamp())
#     time_from = 0  # Unix epoch
    
#     notifications = fetch_notifications(time_from, time_to)
#     process_notifications(notifications)









# # import frappe
# # import requests
# # import json
# # from datetime import datetime, timedelta
# # from components_core.api.wialon_auth import get_valid_session

# # WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

# # @frappe.whitelist()
# # def fetch_notifications(time_from, time_to):
# #     """Fetch notification events from Wialon for a given time range."""
# #     config = frappe.get_single("Wialon API Configuration")
# #     if not config.resource_id:
# #         frappe.throw("Resource ID not configured in Wialon API Configuration")

# #     session_id = get_valid_session()
    
# #     params = {
# #         "resourceId": int(config.resource_id),
# #         "timeFrom": int(time_from),
# #         "timeTo": int(time_to),
# #         "flags": 0
# #     }
    
# #     try:
# #         response = requests.get(
# #             WIALON_API_URL,
# #             params={"svc": "resource/get_notification_data", "sid": session_id, "params": json.dumps(params)}
# #         )
# #         response.raise_for_status()
# #         data = response.json()
# #         if "error" in data:
# #             frappe.log_error(f"Wialon API Error: {data['error']}", "Wialon Notification Fetch")
# #             return []
# #         return data.get("notifications", [])
# #     except Exception as e:
# #         frappe.log_error(f"Failed to fetch notifications: {str(e)}", "Wialon Notification Fetch")
# #         return []

# # def process_notifications(notifications):
# #     """Process and save notification events to the Wialon Notification DocType."""
# #     for notif in notifications:
# #         event_time = datetime.fromtimestamp(notif["t"])
# #         existing = frappe.get_all("Wialon Notification", filters={
# #             "template_id": notif["id"],
# #             "unit_id": notif["un"],
# #             "event_time": event_time
# #         })
# #         if not existing:
# #             doc = frappe.get_doc({
# #                 "doctype": "Wialon Notification",
# #                 "template_id": notif["id"],
# #                 "unit_id": notif["un"],
# #                 "event_time": event_time,
# #                 "type": notif["tp"],
# #                 "message": notif["txt"],
# #                 "fuel_consumption": notif.get("fuel_consumption", 0),
# #                 "emissions": notif.get("emissions", 0)
# #             })
# #             doc.insert(ignore_permissions=True)
# #             trigger_workflow(notif["tp"], notif["un"])

# # def trigger_workflow(notification_type, unit_id):
# #     """Trigger automated actions based on notification type."""
# #     if notification_type == "speed_violation":
# #         frappe.sendmail(
# #             recipients=["manager@example.com"],
# #             subject="Speed Violation Alert",
# #             message=f"Unit {unit_id} has violated speed limits."
# #         )
# #     elif notification_type == "maintenance_due":
# #         frappe.db.set_value("Unit", unit_id, "next_maintenance", datetime.now() + timedelta(days=90))

# # @frappe.whitelist()
# # def predict_maintenance(unit_id):
# #     """Predict next maintenance date based on historical notifications."""
# #     maintenance_notifs = frappe.get_all("Wialon Notification", filters={
# #         "unit_id": unit_id,
# #         "type": "maintenance_due"
# #     }, fields=["event_time"], order_by="event_time desc")
    
# #     if len(maintenance_notifs) < 2:
# #         return "Insufficient data"
    
# #     intervals = []
# #     for i in range(len(maintenance_notifs) - 1):
# #         interval = (maintenance_notifs[i]["event_time"] - maintenance_notifs[i+1]["event_time"]).days
# #         intervals.append(interval)
    
# #     avg_interval = sum(intervals) / len(intervals)
# #     last_maintenance = maintenance_notifs[0]["event_time"]
# #     next_maintenance = last_maintenance + timedelta(days=avg_interval)
# #     return next_maintenance.strftime("%Y-%m-%d")

# # @frappe.whitelist()
# # def fetch_and_save_notifications():
# #     """Fetch and save notifications for the last 15 minutes."""
# #     now = datetime.now()
# #     time_to = int(now.timestamp())
# #     time_from = int((now - timedelta(minutes=15)).timestamp())
    
# #     notifications = fetch_notifications(time_from, time_to)
# #     process_notifications(notifications)

# # # Added new function to fetch all past notifications from epoch to now
# # @frappe.whitelist()
# # def fetch_all_past_notifications():
# #     """Fetch and save all past notifications from the beginning to now."""
# #     now = datetime.now()
# #     time_to = int(now.timestamp())
# #     time_from = 0  # Unix epoch, to fetch all historical data
    
# #     notifications = fetch_notifications(time_from, time_to)
# #     process_notifications(notifications)









# # # import frappe
# # # import requests
# # # import json
# # # from datetime import datetime, timedelta
# # # from components_core.api.wialon_auth import get_valid_session

# # # WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

# # # @frappe.whitelist()
# # # def fetch_notifications(time_from, time_to):
# # #     """Fetch notification events from Wialon for a given time range."""
# # #     config = frappe.get_single("Wialon API Configuration")
# # #     if not config.resource_id:
# # #         frappe.throw("Resource ID not configured in Wialon API Configuration")

# # #     session_id = get_valid_session()
    
# # #     params = {
# # #         "resourceId": int(config.resource_id),
# # #         "timeFrom": int(time_from),
# # #         "timeTo": int(time_to),
# # #         "flags": 0
# # #     }
    
# # #     try:
# # #         response = requests.get(
# # #             WIALON_API_URL,
# # #             params={"svc": "resource/get_notification_data", "sid": session_id, "params": json.dumps(params)}
# # #         )
# # #         response.raise_for_status()
# # #         data = response.json()
# # #         if "error" in data:
# # #             frappe.log_error(f"Wialon API Error: {data['error']}", "Wialon Notification Fetch")
# # #             return []
# # #         return data.get("notifications", [])
# # #     except Exception as e:
# # #         frappe.log_error(f"Failed to fetch notifications: {str(e)}", "Wialon Notification Fetch")
# # #         return []

# # # def process_notifications(notifications):
# # #     """Process and save notification events to the Wialon Notification DocType."""
# # #     for notif in notifications:
# # #         event_time = datetime.fromtimestamp(notif["t"])
# # #         existing = frappe.get_all("Wialon Notification", filters={
# # #             "template_id": notif["id"],
# # #             "unit_id": notif["un"],
# # #             "event_time": event_time
# # #         })
# # #         if not existing:
# # #             doc = frappe.get_doc({
# # #                 "doctype": "Wialon Notification",
# # #                 "template_id": notif["id"],
# # #                 "unit_id": notif["un"],
# # #                 "event_time": event_time,
# # #                 "type": notif["tp"],
# # #                 "message": notif["txt"],
# # #                 "fuel_consumption": notif.get("fuel_consumption", 0),
# # #                 "emissions": notif.get("emissions", 0)
# # #             })
# # #             doc.insert(ignore_permissions=True)
# # #             trigger_workflow(notif["tp"], notif["un"])

# # # def trigger_workflow(notification_type, unit_id):
# # #     """Trigger automated actions based on notification type."""
# # #     if notification_type == "speed_violation":
# # #         frappe.sendmail(
# # #             recipients=["manager@example.com"],
# # #             subject="Speed Violation Alert",
# # #             message=f"Unit {unit_id} has violated speed limits."
# # #         )
# # #     elif notification_type == "maintenance_due":
# # #         frappe.db.set_value("Unit", unit_id, "next_maintenance", datetime.now() + timedelta(days=90))

# # # @frappe.whitelist()
# # # def predict_maintenance(unit_id):
# # #     """Predict next maintenance date based on historical notifications."""
# # #     maintenance_notifs = frappe.get_all("Wialon Notification", filters={
# # #         "unit_id": unit_id,
# # #         "type": "maintenance_due"
# # #     }, fields=["event_time"], order_by="event_time desc")
    
# # #     if len(maintenance_notifs) < 2:
# # #         return "Insufficient data"
    
# # #     intervals = []
# # #     for i in range(len(maintenance_notifs) - 1):
# # #         interval = (maintenance_notifs[i]["event_time"] - maintenance_notifs[i+1]["event_time"]).days
# # #         intervals.append(interval)
    
# # #     avg_interval = sum(intervals) / len(intervals)
# # #     last_maintenance = maintenance_notifs[0]["event_time"]
# # #     next_maintenance = last_maintenance + timedelta(days=avg_interval)
# # #     return next_maintenance.strftime("%Y-%m-%d")

# # # @frappe.whitelist()
# # # def fetch_and_save_notifications():
# # #     """Fetch and save notifications for the last 15 minutes."""
# # #     now = datetime.now()
# # #     time_to = int(now.timestamp())
# # #     time_from = int((now - timedelta(minutes=15)).timestamp())
    
# # #     notifications = fetch_notifications(time_from, time_to)
# # #     process_notifications(notifications)