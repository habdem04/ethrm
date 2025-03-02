import frappe
import requests
import json
from datetime import datetime

@frappe.whitelist()
def sync_employee_to_xaf(doc, method):
    """Sync Employee data from ERPNext to XAF System using OData endpoints."""
    payload = {}
    response = None

    try:
        employee_id = doc.name
        frappe.log(f"Sync triggered for Employee {employee_id}")

        # Fetch linked department details if available
        department_id = None
        department_name = None
        if doc.department:
            department_doc = frappe.get_doc("Department", doc.department)
            department_id = getattr(department_doc, 'custom_payroll_dept_id', None)
            department_name = department_doc.department_name
        else:
            frappe.log("No department linked for this employee.")

        # Ensure DepartmentID is an integer (if it's not None)
        if department_id is not None:
            department_id = int(department_id)

        # Construct full payload for update operations
        payload = {
            "EmployeeID": employee_id if employee_id else None,
            "FullName": doc.employee_name if doc.employee_name else None,
            "BasicSalary": float(doc.custom_basic_salary) if doc.custom_basic_salary else None,
            "WorkHour": int(doc.custom_workhour) if doc.custom_workhour else 208,
            "DepartmentID": department_id if department_id is not None else None,
            "Active": doc.status == "Active" if doc.status else None,
            "Pensioned": bool(doc.custom_pensioned) if doc.custom_pensioned is not None else None,
            "Regular": doc.employment_type == "Full-time" if doc.employment_type else None,
            "ModeofPay": getattr(doc, 'salary_mode', None) if getattr(doc, 'salary_mode', None) else None,
            "Labourunionmember": bool(doc.custom_labour_union) if doc.custom_labour_union is not None else None,
            "DateOfemployment": _format_date(doc.date_of_joining) if doc.date_of_joining else None,
            "DateOfBirth": _format_date(doc.date_of_birth) if doc.date_of_birth else None,
            "Position": getattr(doc, 'designation', None) if getattr(doc, 'designation', None) else None,
            "SalaryGrade": getattr(doc, 'grade', None) if getattr(doc, 'grade', None) else None,
            "CostCenter": getattr(doc, 'payroll_cost_center', None) if getattr(doc, 'payroll_cost_center', None) else None,
            "TINo": getattr(doc, 'custom_tin', None) if getattr(doc, 'custom_tin', None) else None,
            "AmharicFullName": getattr(doc, 'custom_amharic_full_name', None) if getattr(doc, 'custom_amharic_full_name', None) else None,
            "PensionNo": getattr(doc, 'custom_pension_no', None) if getattr(doc, 'custom_pension_no', None) else None
        }

        frappe.log(f"Constructed Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        # Authenticate to obtain token
        token = authenticate_xaf()
        frappe.log(f"Using Token: {token}")

        base_url = "http://192.168.8.3/hrmwa"
        employee_endpoint = f"{base_url}/api/odata/Employee"
        # Common headers with Expect disabled
        common_headers = {
            "Authorization": f"Bearer {token}",
            "Expect": "",
            "Content-Type": "application/json"
        }

        # Check if employee exists by sending a GET request to the employee endpoint
        check_employee_url = f"{employee_endpoint}('{employee_id}')"
        check_response = requests.get(check_employee_url, headers=common_headers, timeout=10)

        if check_response.status_code == 200:
            # Employee exists, update it with PATCH request
            response = requests.patch(
                check_employee_url,
                json=payload,
                headers=common_headers,
                timeout=10
            )
            frappe.log(f"Employee exists, updating with PATCH: {response.status_code} - {response.text}")
        elif check_response.status_code == 404:
            # Employee does not exist, insert new one with POST request
            post_url = f"{employee_endpoint}"
            response = requests.post(
                post_url,
                json=payload,
                headers=common_headers,
                timeout=10
            )
            frappe.log(f"Employee does not exist, inserting with POST: {response.status_code} - {response.text}")
        else:
            # Handle unexpected status codes from the GET request
            frappe.throw(f"Error checking employee existence: {check_response.status_code} - {check_response.text}")

        response.raise_for_status()

    except Exception as e:
        error_response = response.text if response else 'N/A'
        frappe.log_error(
            title="Employee Sync Error",
            message=f"Error: {str(e)}\nPayload: {json.dumps(payload, indent=2, ensure_ascii=False)}\nResponse: {error_response}"
        )
        frappe.throw(f"Sync failed: {str(e)}")

def _format_date(date_val):
    """Format date as ISO 8601 string (YYYY-MM-DDTHH:MM:SSZ)"""
    if isinstance(date_val, datetime):
        return date_val.strftime("%Y-%m-%dT%H:%M:%SZ") if date_val else None
    return None

def authenticate_xaf():
    """Authenticate to XAF API and retrieve the token (using POST request)."""
    base_url = "http://192.168.8.3/hrmwa"
    auth_url = f"{base_url}/api/Authentication/Authenticate"

    # The authentication payload as a dictionary
    payload = {
        "UserName": "Admin",
        "Password": "123"
    }

    # The headers for the request
    headers = {
        "accept": "*/*",
        "Content-Type": "application/json;odata.metadata=minimal;odata.streaming=true",
        "Expect": ""
    }

    try:
        # Perform the POST request to authenticate and get the token
        response = requests.post(auth_url, json=payload, headers=headers, timeout=10)

        # Log full response details for debugging
        frappe.log(f"Auth Response: {response.status_code} - {response.text}")
        frappe.log(f"Auth Response Headers: {response.headers}")

        # Raise an exception if the response status is not 200 OK
        response.raise_for_status()

        # Use plain text response as the token (do not attempt JSON parsing)
        token = response.text.strip()

        if not token:
            frappe.throw("Authentication failed: Token not found in response.")

        return token
    except requests.exceptions.RequestException as e:
        error_response = response.text if response else 'N/A'
        frappe.log_error(
            title="Auth Failed",
            message=f"Auth Error: {str(e)}\nResponse: {error_response}"
        )
        frappe.throw("Authentication failed")
