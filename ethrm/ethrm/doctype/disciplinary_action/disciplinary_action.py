# Copyright (c) 2025, ELIF TECHNOLOGIES PLC and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
from frappe import _

class DisciplinaryAction(Document):
	pass


class DisciplinaryAction(Document):
    def validate(self):
        if self.is_file_attached:
            # Query the File doctype to see if there is an attachment for this document
            file_exists = frappe.db.exists("File", {
                "attached_to_doctype": self.doctype,
                "attached_to_name": self.name
            })
            if not file_exists:
                frappe.throw(_("A file attachment is required when 'is_file_attached' is checked."))
