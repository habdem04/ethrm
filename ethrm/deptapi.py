import frappe
import requests
import json
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote

@frappe.whitelist()
def sync_department_to_xaf(doc, method):
    """Sync Department data from ERPNext to the XAF System using OData endpoints."""
    payload = {}
    response = None

    try:
        # Extract field values from the document using .get()
        department_id = doc.get('custom_payroll_dept_id')
        department_name = doc.department_name.strip() if doc.department_name else None
        # Cost center is optional for .NET, so we don't enforce it
        cost_center = doc.payroll_cost_center.strip() if doc.payroll_cost_center else None

        # Log the retrieved values
        frappe.log(f"[DEBUG] Retrieved Department ID: {department_id}")
        frappe.log(f"[DEBUG] Retrieved Department Name: {department_name}")
        frappe.log(f"[DEBUG] Retrieved Cost Center: {cost_center}")

        # Input Validation: Department ID and Name are required.
        if department_id is None or str(department_id).strip() == '' or not department_name:
            frappe.throw("Department ID and Name are required fields.")

        # Convert Department ID to integer
        try:
            department_id_int = int(department_id)
        except ValueError:
            frappe.throw(f"Department ID '{department_id}' is not a valid integer.")

        frappe.log(f"[INFO] Sync triggered for Department {department_id_int} - {department_name}")

        # Construct payload for the API request
        payload = {
            "DeptCode": department_id,   # using custom_payroll_dept_id directly
            "Name": department_name,
            "CostCenter": cost_center  # Optional field; can be null
        }

        frappe.log(f"[DEBUG] Constructed Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        # Authenticate to obtain the token
        token = authenticate_xaf()
        frappe.log(f"[INFO] Obtained Token: {token}")

        # Base URL and Endpoints
        base_url = "http://192.168.8.3/hrmwa"
        department_endpoint = f"{base_url}/api/odata/Department"

        # URL-encode the department ID for safe usage in URLs
        department_id_encoded = quote(str(department_id_int))

        # Common headers
        common_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Initialize a session with retries for network resilience
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PATCH"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        frappe.log("[DEBUG] Prepared session and headers.")

        # Check if the department exists by sending a GET request
        check_department_url = f"{department_endpoint}({department_id_int})"
        frappe.log(f"[DEBUG] Sending GET request to: {check_department_url}")
        frappe.log(f"[DEBUG] Headers: {json.dumps(common_headers, indent=2)}")
        check_response = session.get(check_department_url, headers=common_headers, timeout=30)
        frappe.log(f"[DEBUG] Check Department Response: {check_response.status_code} - {check_response.text}")

        if check_response.status_code == 200:
            # Department exists, update it with PATCH request
            response = session.patch(
                check_department_url,
                json=payload,
                headers=common_headers,
                timeout=30
            )
            frappe.log(f"[INFO] Department exists, updated with PATCH: {response.status_code} - {response.text}")
        elif check_response.status_code == 404:
            # Department does not exist, create it with POST request
            response = session.post(
                department_endpoint,
                json=payload,
                headers=common_headers,
                timeout=30
            )
            frappe.log(f"[INFO] Department does not exist, created with POST: {response.status_code} - {response.text}")
        else:
            frappe.throw(f"Error checking department existence: {check_response.status_code} - {check_response.text}")

        frappe.log(f"[DEBUG] Response Status Code: {response.status_code}")
        frappe.log(f"[DEBUG] Response Headers: {response.headers}")
        frappe.log(f"[DEBUG] Response Text: {response.text}")

        response.raise_for_status()
        frappe.log(f"[INFO] Sync successful for Department {department_id_int}")

    except Exception as e:
        error_response = response.text if response and hasattr(response, 'text') else 'N/A'
        frappe.log_error(
            title="Department Sync Error",
            message=f"Error: {str(e)}\nPayload: {json.dumps(payload, indent=2)}\nResponse: {error_response}"
        )
        frappe.throw(f"Department Sync Error: {str(e)}")

def authenticate_xaf():
    """Authenticate to XAF API and retrieve the token (using POST request)."""
    base_url = "http://192.168.8.3/hrmwa"
    auth_url = f"{base_url}/api/Authentication/Authenticate"

    # The authentication payload as a dictionary
    payload = {
        "UserName": "Admin",  # Replace with your actual username
        "Password": "123"     # Replace with your actual password
    }

    headers = {
        "accept": "*/*",
        "Content-Type": "application/json",
        "Expect": ""
    }

    try:
        response = requests.post(auth_url, json=payload, headers=headers, timeout=10)
        frappe.log(f"Auth Response: {response.status_code} - {response.text}")
        frappe.log(f"Auth Response Headers: {response.headers}")
        response.raise_for_status()
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
