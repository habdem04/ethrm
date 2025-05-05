import frappe

@frappe.whitelist()
def on_employee_created(doc, method):
    """
    After inserting an Employee record, if employment_type == 'Probation',
    create a linked Employee Probation record—unless one already exists.
    """
    if doc.employment_type != "Probation":
        return

    # if there's already a probation record for this Employee, do nothing
    exists = frappe.db.exists(
        "Employee Probation",
        {"employee": doc.name}
    )
    if exists:
        return {"message": "Probation record already exists for employee {0}".format(doc.name)}

    # (optional) pull probation days from settings
    probation_days = 0
    try:
        settings = frappe.get_single("Probation Setting")
        probation_days = int(settings.probation_in_days or 0)
    except frappe.DoesNotExistError:
        frappe.log_error("Probation Setting not found", "Probation Handler")

    # build the new probation doc
    probation = frappe.new_doc("Employee Probation")
    probation.employee = doc.name
    probation.full_name = doc.employee_name
    probation.salary_grade = doc.grade  # Make sure 'doc.grade' is the intended field
    probation.in_probation_days = probation_days
    probation.end_date_gc = doc.custom_probation_end_date

    probation.insert(ignore_permissions=True)
    frappe.db.commit()

    # Create a confirmation message
    confirmation_message = "Probation record '{0}' successfully created for employee '{1}'.".format(probation.name, doc.name)
    frappe.msgprint(confirmation_message)  # This displays a message on the front-end (if applicable)
    
    return {"success": True, "message": confirmation_message}