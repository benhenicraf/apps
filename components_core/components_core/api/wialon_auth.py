import frappe
import requests
import json
from frappe.utils import now_datetime, get_datetime
from datetime import timedelta

WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

def get_wialon_credentials():
    """Fetch API token from Frappe Configuration DocType."""
    config = frappe.get_single("Wialon API Configuration")
    return config.api_token if config else None

def validate_session(session_id):
    """Check if the session is still valid."""
    try:
        response = requests.get(
            WIALON_API_URL,
            params={"svc": "core/check_session", "sid": session_id},
            timeout=5
        )
        return response.json().get("error", 1) == 0
    except Exception as e:
        frappe.log_error(f"Session validation failed: {str(e)}")
        return False

def fetch_resource_id(session_id):
    """Fetch Resource ID after successful authentication."""
    params = {
        "spec": {
            "itemsType": "avl_resource",
            "propName": "sys_name",
            "propValueMask": "*",
            "sortType": "sys_name",
            "propType": "property"
        },
        "force": 1,
        "flags": 1,
        "from": 0,
        "to": 1
    }

    try:
        response = requests.post(
            f"{WIALON_API_URL}?svc=core/search_items&sid={session_id}",
            data={"params": json.dumps(params)},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["id"]

    except requests.exceptions.RequestException as e:
        frappe.log_error(f"Failed fetching resource ID: {str(e)}")

    return None

@frappe.whitelist() 
def authenticate():
    """Authenticate with Wialon, store session and fetch Resource ID."""
    config = frappe.get_single("Wialon API Configuration")

    if not config.api_token:
        return {"error": "API Token not configured in 'Wialon API Configuration'"}

    try:
        response = requests.get(
            WIALON_API_URL,
            params={
                "svc": "token/login",
                "params": json.dumps({"token": config.api_token})
            },
            timeout=10
        )
        response.raise_for_status()

        auth_data = response.json()
        if "eid" in auth_data:
            session_id = auth_data["eid"]
            resource_id = fetch_resource_id(session_id)

            # Use a transaction-free update to avoid locks
            frappe.db.set_value("Wialon API Configuration", None, {
                "session_id": session_id,
                "last_authenticated": datetime.now(),
                "resource_id": resource_id
            })
            frappe.db.commit()  # ✅ Fix: Force commit transaction

            return {
                "success": True,
                "session_id": session_id,
                "resource_id": resource_id
            }

        return {"error": "Authentication failed: Invalid response"}

    except requests.exceptions.RequestException as e:
        frappe.log_error(f"Wialon Auth Error: {str(e)}")
        return {"error": f"Connection error: {str(e)}"}

@frappe.whitelist()
def get_valid_session():
    """Ensure session is valid before making Wialon API requests"""
    config = frappe.get_single("Wialon API Configuration")

    # If session ID exists and is not expired, return it
    if config.session_id and config.last_authenticated:
        if isinstance(config.last_authenticated, str):
            config.last_authenticated = datetime.fromisoformat(config.last_authenticated)

        session_age = (datetime.now() - config.last_authenticated).total_seconds()
        if session_age < 3600:  # Valid for 1 hour
            return {"session_id": config.session_id, "resource_id": config.resource_id}

    # Otherwise, authenticate and return new session
    return authenticate()










# import frappe
# import requests
# import json
# from datetime import datetime

# WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

# def validate_session(session_id):
#     """Check if session is still valid"""
#     try:
#         response = requests.get(
#             WIALON_API_URL,
#             params={"svc": "core/check_session", "sid": session_id},
#             timeout=5
#         )
#         return response.json().get("error", 1) == 0
#     except Exception as e:
#         frappe.log_error(f"Session validation failed: {str(e)}")
#         return False

# def fetch_resource_id(session_id):  # ✅ Newly Added Function
#     """Fetch Resource ID after successful authentication"""
#     params = {
#         "spec": {
#             "itemsType": "avl_resource",
#             "propName": "sys_name",
#             "propValueMask": "*",
#             "sortType": "sys_name",
#             "propType": "property"
#         },
#         "force": 1,
#         "flags": 1,
#         "from": 0,
#         "to": 1
#     }

#     try:
#         response = requests.post(
#             f"{WIALON_API_URL}?svc=core/search_items&sid={session_id}",
#             data={"params": json.dumps(params)},
#             timeout=10
#         )
#         response.raise_for_status()
#         data = response.json()

#         if "items" in data and len(data["items"]) > 0:
#             return data["items"][0]["id"]

#     except requests.exceptions.RequestException as e:
#         frappe.log_error(f"Failed fetching resource ID: {str(e)}")

#     return None

# @frappe.whitelist(allow_guest=True)
# def authenticate():
#     """Enhanced authentication with error handling and resource ID fetching"""
#     config = frappe.get_single("Wialon API Configuration")

#     if not config.api_token:
#         return {"error": "API Token not configured"}

#     try:
#         response = requests.get(
#             WIALON_API_URL,
#             params={
#                 "svc": "token/login",
#                 "params": json.dumps({"token": config.api_token})
#             },
#             timeout=10
#         )
#         response.raise_for_status()

#         auth_data = response.json()
#         if "eid" in auth_data:
#             config.session_id = auth_data["eid"]
#             config.last_authenticated = datetime.now()

#             # ✅ New modification: Fetching resource_id after session creation
#             resource_id = fetch_resource_id(config.session_id)
#             if resource_id:
#                 config.resource_id = resource_id  # ✅ New field stored in Doctype
#             else:
#                 frappe.log_error("Resource ID fetching failed.")

#             config.save()

#             # ✅ Modified response including resource_id
#             return {
#                 "success": True,
#                 "session_id": auth_data["eid"],
#                 "resource_id": resource_id
#             }

#         return {"error": "Authentication failed: Invalid response"}

#     except requests.exceptions.RequestException as e:
#         frappe.log_error(f"Wialon Auth Error: {str(e)}")
#         return {"error": f"Connection error: {str(e)}"}

# @frappe.whitelist()
# def get_valid_session():
#     """Get session with validation and renewal"""
#     config = frappe.get_single("Wialon API Configuration")

#     if config.session_id and validate_session(config.session_id):
#         return config.session_id

#     auth_result = authenticate()
#     if "session_id" in auth_result:
#         return auth_result["session_id"]

#     frappe.throw("Failed to establish Wialon session")









########***********Working Code***************#############
# import frappe
# import requests
# import json
# from datetime import datetime

# WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

# def validate_session(session_id):
#     """Check if session is still valid"""
#     try:
        
#         response = requests.get(
#             f"{WIALON_API_URL}",
#             params={"svc": "core/check_session", "sid": session_id},
#             timeout=5
#         )
#         return response.json().get("error", 1) == 0
#     except Exception as e:
#         frappe.log_error(f"Session validation failed: {str(e)}")
#         return False

# # Grok modified: Removed allow_guest=True for security unless explicitly needed
# @frappe.whitelist()
# def authenticate():
#     """Enhanced authentication with error handling"""
#     config = frappe.get_single("Wialon API Configuration")
    
#     if not config.api_token:
#         return {"error": "API Token not configured"}

#     try:
#         response = requests.get(
#             f"{WIALON_API_URL}",
#             params={
#                 "svc": "token/login",
#                 "params": json.dumps({"token": config.api_token})
#             },
#             timeout=10
#         )
#         response.raise_for_status()
        
#         auth_data = response.json()
#         if "eid" in auth_data:
#             config.session_id = auth_data["eid"]
#             config.last_authenticated = datetime.now()
#             config.save()
#             return {"success": True, "session_id": auth_data["eid"]}
            
#         return {"error": "Authentication failed: Invalid response"}
        
#     except requests.exceptions.RequestException as e:
#         frappe.log_error(f"Wialon Auth Error: {str(e)}")
#         return {"error": f"Connection error: {str(e)}"}

# # Grok modified: Removed allow_guest=True for security
# @frappe.whitelist()
# def get_valid_session():
#     """Get session with validation and renewal"""
#     config = frappe.get_single("Wialon API Configuration")
    
#     if config.session_id and validate_session(config.session_id):
#         return config.session_id
        
#     auth_result = authenticate()
#     if "session_id" in auth_result:
#         return auth_result["session_id"]
        
#     frappe.throw("Failed to establish Wialon session")









# import frappe
# import requests
# import json
# from datetime import datetime

# WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

# def validate_session(session_id):
#     """Check if session is still valid"""
#     try:
#         response = requests.post(
#             f"{WIALON_API_URL}?svc=core/check_session",
#             data={"sid": session_id},
#             timeout=5
#         )
#         return response.json().get("error") == 0
#     except Exception as e:
#         frappe.log_error(f"Session validation failed: {str(e)}")
#         return False

# @frappe.whitelist(allow_guest=True)
# def authenticate():
#     """Enhanced authentication with error handling"""
#     config = frappe.get_single("Wialon API Configuration")
    
#     if not config.api_token:
#         return {"error": "API Token not configured"}

#     try:
#         response = requests.post(
#             f"{WIALON_API_URL}?svc=token/login",
#             data={"params": json.dumps({"token": config.api_token})},
#             timeout=10
#         )
#         response.raise_for_status()
        
#         auth_data = response.json()
#         if "eid" in auth_data:
#             config.session_id = auth_data["eid"]
#             config.last_authenticated = datetime.now()
#             config.save()
#             return {"success": True, "session_id": auth_data["eid"]}
            
#         return {"error": "Authentication failed: Invalid response"}
        
#     except requests.exceptions.RequestException as e:
#         frappe.log_error(f"Wialon Auth Error: {str(e)}")
#         return {"error": f"Connection error: {str(e)}"}

# @frappe.whitelist(allow_guest=True)
# def get_valid_session():
#     """Get session with validation and renewal"""
#     config = frappe.get_single("Wialon API Configuration")
    
#     if config.session_id and validate_session(config.session_id):
#         return config.session_id
        
#     auth_result = authenticate()
#     if "session_id" in auth_result:
#         return auth_result["session_id"]
        
#     frappe.throw("Failed to establish Wialon session")