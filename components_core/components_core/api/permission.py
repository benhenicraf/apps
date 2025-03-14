# File: components_core/api/permission.py

import frappe

def check_access(doc, ptype, user):
    """Allow only System Managers to access Wialon API Configuration."""
    if "System Manager" in frappe.get_roles(user):
        return True
    return False
