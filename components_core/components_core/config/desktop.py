from frappe import _

def get_data():
    return [
        {
            "module_name": "Components Core",
            "category": "Modules",
            "label": _("Wialon Monitoring"),
            "icon": "octicon octicon-location",
            "type": "module",
            "color": "green",
            "link": "/app/wialon-api-configuration"
        },
        {
            "module_name": "Wialon API Configuration",
            "category": "Integrations",
            "label": _("Wialon API Configuration"),
            "icon": "octicon octicon-gear",
            "type": "doctype",
            "doctype": "Wialon API Configuration",
            "link": "/app/wialon-api-configuration"
        }
    ]
