// Copyright (c) 2025, Auwal Isiaku Mafindi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Laundry Order', {
    refresh: function(frm) {
        if(frm.doc.docstatus === 1) {  // Only allow for submitted orders
            // Always show view invoice button (since invoice is created automatically on submit)
            if(frm.doc.invoice_number) {
                // Show view invoice button
                frm.add_custom_button(__('View Invoice'), function() {
                    frappe.set_route("Form", "Sales Invoice", frm.doc.invoice_number);
                }, __("Accounting"));
                
                // Show payment button
                frm.add_custom_button(__('Make Payment'), function() {
                    frappe.call({
                        method: "frappe.client.get",
                        args: {
                            doctype: "Sales Invoice",
                            name: frm.doc.invoice_number
                        },
                        callback: function(r) {
                            if(r.message && r.message.outstanding_amount > 0) {
                                frappe.new_doc("Payment Entry", {
                                    payment_type: "Receive",
                                    party_type: "Customer",
                                    party: r.message.customer,
                                    paid_amount: r.message.outstanding_amount,
                                    references: [{
                                        reference_doctype: "Sales Invoice",
                                        reference_name: frm.doc.invoice_number,
                                        allocated_amount: r.message.outstanding_amount
                                    }],
                                    laundry_order: frm.doc.name
                                });
                            } else {
                                frappe.msgprint(__("No outstanding amount to pay"));
                            }
                        }
                    });
                }, __("Accounting"));
            } else {
                // Invoice creation failed during submission, provide a manual button
                frm.add_custom_button(__('Create Invoice'), function() {
                    frappe.call({
                        method: "create_sales_invoice",
                        doc: frm.doc,
                        callback: function(r) {
                            if(r.message) {
                                frm.reload_doc();
                            }
                        }
                    });
                }, __("Accounting"));
                
                // Show warning that invoice creation failed during submission
                frm.page.set_indicator(__("Invoice Creation Failed"), "red");
            }
        }
    },
    
    after_save: function(frm) {
        // Clear any custom indicators when the document is saved
        if(frm.doc.docstatus === 0) {
            frm.page.clear_indicator();
        }
    }
});

