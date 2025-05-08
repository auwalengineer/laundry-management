# laundry_management/setup/install.py
#import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def after_install():
    """Run setup operations after app installation"""
    create_laundry_custom_fields()
    create_property_setters()

def create_laundry_custom_fields():
    """Create custom fields in Sales Invoice and Payment Entry for Laundry integration"""
    custom_fields = {
        "Sales Invoice": [
            {
                "fieldname": "laundry_management_section",
                "fieldtype": "Section Break",
                "insert_after": "customer_section",
                "label": "Laundry Management",
                "collapsible": 1
            },
            {
                "fieldname": "laundry_order",
                "fieldtype": "Link",
                "insert_after": "laundry_management_section",
                "label": "Laundry Order",
                "options": "Laundry Order",
                "in_standard_filter": 1,
                "in_global_search": 1,
                "fetch_from": "",
                "fetch_if_empty": 1
            },
            {
                "fieldname": "laundry_status",
                "fieldtype": "Read Only",
                "insert_after": "laundry_order",
                "label": "Laundry Status",
                "fetch_from": "laundry_order.status"
            },
            {
                "fieldname": "laundry_delivery_date",
                "fieldtype": "Read Only",
                "insert_after": "laundry_status",
                "label": "Promised Delivery Date",
                "fetch_from": "laundry_order.promised_delivery_date"
            }
        ],
        "Payment Entry": [
            {
                "fieldname": "laundry_management_section",
                "fieldtype": "Section Break",
                "insert_after": "subscription_section",
                "label": "Laundry Management",
                "collapsible": 1
            },
            {
                "fieldname": "laundry_order",
                "fieldtype": "Link",
                "insert_after": "laundry_management_section",
                "label": "Laundry Order",
                "options": "Laundry Order",
                "in_standard_filter": 1
            }
        ]
    }
    
    create_custom_fields(custom_fields)
    frappe.db.commit()
    frappe.msgprint("Custom fields for Laundry Management accounting integration created successfully")

def create_property_setters():
    """Create property setters for enabling better integration"""
    property_setters = [
        {
            "doctype": "Property Setter",
            "doc_type": "Laundry Order",
            "property": "allow_auto_repeat",
            "value": "1",
            "property_type": "Check"
        },
        {
            "doctype": "Property Setter",
            "doc_type": "Laundry Order",
            "property": "show_in_global_search",
            "value": "1",
            "property_type": "Check"
        }
    ]
    
    for ps in property_setters:
        if not frappe.db.exists("Property Setter", {
            "doc_type": ps["doc_type"],
            "property": ps["property"]
        }):
            doc = frappe.get_doc(ps)
            doc.insert()
    
    frappe.db.commit()
