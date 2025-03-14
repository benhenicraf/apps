import frappe
import requests
import json
from datetime import datetime
from components_core.api.wialon_auth import validate_session, get_valid_session

WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

@frappe.whitelist()
def get_live_positions(limit=100, resource_id=None):
    """Fetch live positions from Wialon API with batch processing and caching.

    Args:
        limit (int): Maximum number of units to fetch (default: 100).
        resource_id (int, optional): Filter units by resource ID.

    Returns:
        list: List of live unit positions.
    """
    try:
        # Check for cached results first (reduces API load)
        cache_key = f"wialon_live_positions_{resource_id or 'all'}"
        cached_positions = frappe.cache().get_value(cache_key)

        if cached_positions:
            return cached_positions

        # Retrieve valid session ID
        session_id = get_valid_session()
        if not session_id:
            return {"error": "Failed to establish a valid Wialon session"}

        # Construct API request parameters
        spec = {
            "itemsType": "avl_unit",
            "propName": "sys_name",
            "propValueMask": "*",
            "sortType": "sys_name"
        }

        # Filter by resource ID if provided
        if resource_id:
            spec["propName"] = "rel_avl_resource_id"
            spec["propValueMask"] = str(resource_id)

        params = {
            "svc": "core/search_items",
            "params": json.dumps({
                "spec": spec,
                "force": 1,
                "flags": 1025,
                "from": 0,
                "to": limit
            }),
            "sid": session_id
        }

        # Make API request
        response = requests.post(WIALON_API_URL, data=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Handle errors
        if "items" not in data:
            return {"error": f"Failed to fetch live positions: {data.get('error', 'Unknown error')}"}

        # Process API response
        live_positions = []
        for unit in data["items"]:
            if "pos" in unit:
                # Convert timestamp to readable format
                last_updated = datetime.fromtimestamp(unit["pos"]["t"]).strftime("%Y-%m-%d %H:%M:%S")
                live_positions.append({
                    "unit_id": unit["id"],
                    "name": unit["nm"],
                    "latitude": unit["pos"]["y"],
                    "longitude": unit["pos"]["x"],
                    "speed": unit["pos"]["s"],
                    "last_updated": last_updated
                })

        # Cache the results to reduce API load (valid for 2 minutes)
        frappe.cache().set_value(cache_key, live_positions, expires_in_sec=120)

        return live_positions

    except requests.exceptions.RequestException as e:
        frappe.log_error(f"Error fetching Wialon live positions: {str(e)}", "Wialon API")
        return {"error": f"Failed to fetch live positions: {str(e)}"}










# import frappe
# import requests
# import json
# from datetime import datetime

# # Assuming these functions exist in wialon_auth.py
# from components_core.api.wialon_auth import validate_session, get_valid_session

# @frappe.whitelist()
# def get_live_positions(limit=100, resource_id=None):
#     """Fetch live positions from Wialon API with session validation and optional resource filtering.
    
#     Args:
#         limit (int): Maximum number of units to fetch (default: 100).
#         resource_id (int, optional): Filter units by resource ID.
#     """
#     try:
#         # Retrieve API token and session ID
#         api_token = frappe.db.get_single_value("Wialon API Configuration", "api_token")
#         session_id = frappe.db.get_single_value("Wialon API Configuration", "session_id")

#         if not api_token or not session_id:
#             return {"error": "API Token or Session ID missing"}

#         # Validate session; refresh if invalid
#         if not validate_session(session_id):
#             session_id = get_valid_session()
#             if not session_id:
#                 return {"error": "Failed to establish a valid Wialon session"}

#         url = "https://hst-api.wialon.com/wialon/ajax.html"
#         spec = {
#             "itemsType": "avl_unit",
#             "propName": "sys_name",
#             "propValueMask": "*",
#             "sortType": "sys_name"
#         }
#         # Add resource filtering if provided
#         if resource_id:
#             spec["propName"] = "rel_avl_resource_id"
#             spec["propValueMask"] = str(resource_id)

#         params = {
#             "svc": "core/search_items",
#             "params": json.dumps({
#                 "spec": spec,
#                 "force": 1,
#                 "flags": 1025,
#                 "from": 0,
#                 "to": limit
#             }),
#             "sid": session_id
#         }

#         response = requests.post(url, data=params)
#         data = response.json()

#         if "items" not in data:
#             return {"error": f"Failed to fetch live positions: {data.get('error', 'Unknown error')}"}

#         live_positions = []
#         for unit in data["items"]:
#             if "pos" in unit:
#                 # Convert timestamp to readable format
#                 last_updated = datetime.fromtimestamp(unit["pos"]["t"]).strftime("%Y-%m-%d %H:%M:%S")
#                 live_positions.append({
#                     "unit_id": unit["id"],
#                     "name": unit["nm"],
#                     "latitude": unit["pos"]["y"],
#                     "longitude": unit["pos"]["x"],
#                     "speed": unit["pos"]["s"],
#                     "last_updated": last_updated
#                 })

#         return live_positions

#     except Exception as e:
#         frappe.log_error(f"Error fetching Wialon live positions: {str(e)}", "Wialon API")
#         return {"error": f"Failed to fetch live positions: {str(e)}"}









################********************working Code****************################

# import frappe
# import requests
# import json

# @frappe.whitelist()
# def get_live_positions():
#     """Fetch live positions from Wialon API"""
#     try:
#         api_token = frappe.db.get_single_value("Wialon API Configuration", "api_token")
#         session_id = frappe.db.get_single_value("Wialon API Configuration", "session_id")

#         if not api_token or not session_id:
#             return {"error": "API Token or Session ID missing"}

#         url = "https://hst-api.wialon.com/wialon/ajax.html"
#         params = {
#             "svc": "core/search_items",
#             "params": json.dumps({
#                 "spec": {
#                     "itemsType": "avl_unit",
#                     "propName": "sys_name",
#                     "propValueMask": "*",
#                     "sortType": "sys_name"
#                 },
#                 "force": 1,
#                 "flags": 1025,
#                 "from": 0,
#                 "to": 100
#             }),
#             "sid": session_id
#         }

#         response = requests.post(url, data=params)
#         data = response.json()

#         if "items" not in data:
#             return {"error": "Failed to fetch live positions"}

#         live_positions = []
#         for unit in data["items"]:
#             if "pos" in unit:
#                 live_positions.append({
#                     "unit_id": unit["id"],
#                     "name": unit["nm"],
#                     "latitude": unit["pos"]["y"],
#                     "longitude": unit["pos"]["x"],
#                     "speed": unit["pos"]["s"],
#                     "last_updated": unit["pos"]["t"]
#                 })

#         return live_positions

#     except Exception as e:
#         frappe.log_error(f"Error fetching Wialon live positions: {str(e)}", "Wialon API")
#         return {"error": "Failed to fetch live positions"}










# # wialon_units.py
# import frappe
# import requests
# import json
# from .wialon_auth import get_valid_session

# WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

# @frappe.whitelist()
# def get_live_positions():
#     """Fetch positions with proper error handling"""
#     try:
#         session_id = get_valid_session()
        
#         # Grok modified: Used GET with params for Wialon API consistency
#         response = requests.get(
#             WIALON_API_URL,
#             params={
#                 "svc": "core/search_items",
#                 "sid": session_id,
#                 "params": json.dumps({
#                     "spec": {
#                         "itemsType": "avl_unit",
#                         "propName": "sys_name",
#                         "propValueMask": "*",
#                         "sortType": "sys_name"
#                     },
#                     "force": 1,
#                     "flags": 1025,
#                     "from": 0,
#                     "to": 0
#                 })
#             },
#             timeout=15
#         )
#         response.raise_for_status()
        
#         data = response.json()
#         if "items" not in data:
#             return {"error": "No units found"}
            
#         return process_units(data["items"])
        
#     except Exception as e:
#         frappe.log_error(f"Position fetch failed: {str(e)}")
#         return {"error": str(e)}

# def process_units(units):
#     """Convert Wialon units to standardized format"""
#     return [
#         {
#             "unit_id": u["id"],
#             "name": u["nm"],
#             "latitude": u["pos"]["y"],
#             "longitude": u["pos"]["x"],
#             "speed": u["pos"]["s"],
#             "last_updated": frappe.utils.format_datetime(frappe.utils.get_datetime(u["pos"]["t"]))
#         }
#         for u in units if "pos" in u
#     ]









# # import frappe
# # import requests
# # import json
# # from .wialon_auth import get_valid_session

# # WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

# # @frappe.whitelist()
# # def get_live_positions():
# #     """Fetch positions with proper error handling"""
# #     try:
# #         session_id = get_valid_session()
        
# #         response = requests.post(
# #             WIALON_API_URL,
# #             data={
# #                 "svc": "core/search_items",
# #                 "sid": session_id,
# #                 "params": json.dumps({
# #                     "spec": {
# #                         "itemsType": "avl_unit",
# #                         "propName": "sys_name",
# #                         "propValueMask": "*",
# #                         "sortType": "sys_name"
# #                     },
# #                     "force": 1,
# #                     "flags": 1025,
# #                     "from": 0,
# #                     "to": 0
# #                 })
# #             },
# #             timeout=15
# #         )
# #         response.raise_for_status()
        
# #         data = response.json()
# #         if "items" not in data:
# #             return {"error": "No units found"}
            
# #         return process_units(data["items"])
        
# #     except Exception as e:
# #         frappe.log_error(f"Position fetch failed: {str(e)}")
# #         return {"error": str(e)}

# # def process_units(units):
# #     """Convert Wialon units to standardized format"""
# #     return [
# #         {
# #             "unit_id": u["id"],
# #             "name": u["nm"],
# #             "latitude": u["pos"]["y"],
# #             "longitude": u["pos"]["x"],
# #             "speed": u["pos"]["s"],
# #             "last_updated": frappe.utils.format_datetime(frappe.utils.get_datetime(u["pos"]["t"]))
# #         }
# #         for u in units if "pos" in u
# #     ]