# laundry_management/laundry_management/doctype/laundry_order/laundry_order.py
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days, get_datetime, now_datetime

class LaundryOrder(Document):
    def validate(self):
        self.validate_delivery_date()
        self.calculate_totals()
        
    def before_submit(self):
        self.update_customer_loyalty_points()
        self.create_sales_invoice()
        
    def validate_delivery_date(self):
        # Calculate the promised delivery date based on service types if not set
        if not self.promised_delivery_date:
            max_turnaround_time = 0
            for item in self.order_items:
                service = frappe.get_doc("Laundry Service Type", item.service_type)
                if service.turnaround_time_hours > max_turnaround_time:
                    max_turnaround_time = service.turnaround_time_hours
                    
            # Add priority-based adjustments
            if self.priority == "Urgent":
                max_turnaround_time = max(1, max_turnaround_time // 2)  # At least 1 hour, but half normal time
            elif self.priority == "High":
                max_turnaround_time = max(2, int(max_turnaround_time * 0.75))  # At least 2 hours, but 75% of normal time
            elif self.priority == "Low":
                max_turnaround_time = int(max_turnaround_time * 1.5)  # 150% of normal time
                
            current_time = get_datetime(self.order_date) or now_datetime()
            self.promised_delivery_date = add_days(current_time, 
                                                max_turnaround_time // 24, 
                                                hours=max_turnaround_time % 24)
            
    def calculate_totals(self):
        self.subtotal = 0
        
        for item in self.order_items:
            # Fetch price from service if not already set
            if not item.unit_price:
                service = frappe.get_doc("Laundry Service Type", item.service_type)
                item.unit_price = service.price_per_unit
                
            item.amount = item.quantity * item.unit_price
            self.subtotal += item.amount
            
        # Calculate total with tax and discount
        if not self.tax_amount:
            self.tax_amount = 0
        if not self.discount_amount:
            self.discount_amount = 0
            
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        
    def update_customer_loyalty_points(self):
        # Add loyalty points based on order total
        if self.status != "Cancelled" and self.docstatus == 1:  # Submitted
            loyalty_points_to_add = int(self.total_amount // 10)  # 1 point for every $10
            
            customer = frappe.get_doc("Laundry Customer", self.customer)
            customer.loyalty_points = customer.loyalty_points + loyalty_points_to_add
            customer.save()
            
            frappe.msgprint(f"Added {loyalty_points_to_add} loyalty points to customer {customer.customer_name}")
            
    def on_update(self):
        # Send notifications when status changes
        if self.has_value_changed("status"):
            # Create a notification for the customer
            if self.status == "Ready for Pickup":
                self.send_ready_notification()
                
    def send_ready_notification(self):

        # Get customer details
        customer = frappe.get_doc("Laundry Customer", self.customer)
        if customer.email:
            # Send email notification
            subject = f"Your laundry order {self.name} is ready for pickup"
            message = f"""
            Dear {customer.customer_name},

            Your laundry order {self.name} is now ready for pickup.

            Order Details:
            - Order Date: {self.order_date}
            - Total Amount: {self.total_amount}

            Thank you for choosing our service!

            Best regards,
            Laundry Management Team
            """
            frappe.sendmail(
                recipients=[customer.email],
                subject=subject,
                message=message
            )
            frappe.msgprint(f"Pickup notification sent to {customer.email}")
    
    def create_sales_invoice(self):
        """Create a Sales Invoice from this Laundry Order"""
        if self.docstatus != 1:
            frappe.throw(_("Order must be submitted before creating an invoice"))
            
        # Check if invoice already exists
        existing_invoice = frappe.db.exists("Sales Invoice", {"laundry_order": self.name})
        if existing_invoice:
            frappe.throw(_("Sales Invoice {} already exists").format(existing_invoice))
        
        # Create new Sales Invoice
        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = self.customer
        invoice.posting_date = frappe.utils.nowdate()
        invoice.due_date = frappe.utils.add_days(frappe.utils.nowdate(), 7)  # Default due date
        invoice.laundry_order = self.name  # Custom field in Sales Invoice
        
        # Add items from Laundry Order
        for item in self.order_items:
            invoice.append("items", {
                "item_code": item.service_type,  # Assuming service types are set up as Items
                "item_name": item.item_description,
                "description": item.item_description,
                "qty": item.quantity,
                "rate": item.unit_price,
                "amount": item.amount,
                "income_account": frappe.db.get_value("Company", invoice.company, "default_income_account")
            })
        
        # Apply taxes, discounts, etc.
        if self.tax_amount:
            invoice.append("taxes", {
                "charge_type": "Actual",
                "account_head": frappe.db.get_value("Company", invoice.company, "default_tax_account"),
                "description": "Tax",
                "tax_amount": self.tax_amount
            })
        
        if self.discount_amount:
            invoice.apply_discount_amount = self.discount_amount
        
        invoice.save()
        invoice.submit()  # Auto-submit if required
        
        frappe.msgprint(_("Sales Invoice {} created successfully").format(invoice.name))
        return invoice.name
