import frappe
import requests
import json
from components_core.api.wialon_auth import get_valid_session

WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

@frappe.whitelist()
def fetch_resources():
    """Fetch all resources available to the user from Wialon using an existing session."""
    
    session_id = get_valid_session()
    if not session_id:
        frappe.throw("Failed to obtain a valid Wialon session.")

    # Fetch resources
    params = {
        "spec": {
            "itemsType": "avl_resource",
            "propName": "sys_name",
            "propValueMask": "*",
            "sortType": "sys_name"
        },
        "force": 1,
        "flags": 1,  # Fetch basic info (name and ID)
        "from": 0,
        "to": 100  # Fetch up to 100 resources
    }

    try:
        response = requests.get(
            WIALON_API_URL,
            params={"svc": "core/search_items", "sid": session_id, "params": json.dumps(params)},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            frappe.log_error(f"Wialon API Error: {data['error']}", "Wialon Fetch Resources")
            return {"error": f"Failed to fetch resources: {data['error']}"}

        return data.get("items", [])

    except requests.exceptions.RequestException as e:
        frappe.log_error(f"Error fetching Wialon resources: {str(e)}", "Wialon API")
        return {"error": f"Failed to fetch resources: {str(e)}"}










# import frappe
# import requests
# import json

# WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

# @frappe.whitelist()
# def fetch_resources():
#     """Fetch all resources available to the user from Wialon."""
#     config = frappe.get_single("Wialon API Configuration")
#     if not config.api_token:
#         frappe.throw("API Token is missing in Wialon API Configuration.")

#     # Authenticate and get session ID
#     response = requests.get(
#         WIALON_API_URL,
#         params={"svc": "token/login", "params": json.dumps({"token": config.api_token})}
#     )
#     response.raise_for_status()
#     data = response.json()
#     if "eid" not in data:
#         frappe.throw("Failed to authenticate with Wialon API.")
#     session_id = data["eid"]

#     # Fetch resources
#     params = {
#         "spec": {
#             "itemsType": "avl_resource",
#             "propName": "sys_name",
#             "propValueMask": "*",
#             "sortType": "sys_name"
#         },
#         "force": 1,
#         "flags": 1,  # Fetch basic info (name and ID)
#         "from": 0,
#         "to": 0
#     }
#     response = requests.get(
#         WIALON_API_URL,
#         params={"svc": "core/search_items", "sid": session_id, "params": json.dumps(params)}
#     )
#     response.raise_for_status()
#     data = response.json()
#     if "error" in data:
#         frappe.throw(f"Error fetching resources: {data['error']}")
#     return data.get("items", [])