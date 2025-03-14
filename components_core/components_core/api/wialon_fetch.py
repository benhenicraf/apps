import frappe
import requests
import json

WIALON_API_URL = "https://hst-api.wialon.com/wialon/ajax.html"

@frappe.whitelist()
def fetch_wialon_units():
    """Fetch all units from Wialon API and store them in Frappe."""
    config = frappe.get_single("Wialon API Configuration")

    if not config.session_id:
        return {"error": "Wialon session ID not found. Try authenticating again."}

    try:
        response = requests.get(
            WIALON_API_URL,
            params={
                "svc": "core/search_items",
                "params": json.dumps({
                    "spec": {"itemsType": "avl_unit", "propName": "sys_name", "propValueMask": "*", "sortType": "sys_name"},
                    "force": 1,
                    "flags": 1,
                    "from": 0,
                    "to": 0
                }),
                "sid": config.session_id
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if "items" in data:
            for unit in data["items"]:
                unit_doc = frappe.get_doc({
                    "doctype": "Wialon Tracked Unit",
                    "unit_id": unit["id"],
                    "unit_name": unit["nm"],
                    "latitude": unit["pos"]["y"] if "pos" in unit else None,
                    "longitude": unit["pos"]["x"] if "pos" in unit else None,
                    "last_update": frappe.utils.now_datetime()
                })
                unit_doc.insert(ignore_permissions=True)

            frappe.db.commit()
            return {"success": f"Fetched {len(data['items'])} units successfully."}

        return {"error": "No units found in Wialon."}

    except requests.exceptions.RequestException as e:
        frappe.log_error(f"Wialon Fetch Units Error: {str(e)}")
        return {"error": f"Connection error: {str(e)}"}
