import frappe
import requests
import json
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote

@frappe.whitelist()
def sync_position_to_xaf(doc, method):
    """Sync Position data from ERPNext to the XAF System using OData endpoints.
    
    Note: The .NET Position table uses an auto-incremented primary key (OID).
    ERPPositionId (mapped to doc.name) is not the primary key, so we use an OData
    filter query to check for an existing record.
    """
    payload = {}
    response = None

    try:
        # Extract field values from the document using .get()
        erp_position_id = doc.name  # ERPPositionId in .NET maps to name in ERPNext
        position_name = doc.designation_name.strip() if doc.designation_name else None  # PositionName

        # Convert 'custom_is_disabled_' (0 or 1) to boolean 'Active' status:
        # Active should be True when custom_is_disabled_ is 0 (enabled)
        # Active should be False when custom_is_disabled_ is 1 (disabled)
        active = True if doc.custom_is_disabled_ == 0 else False

        # Log the retrieved values
        frappe.log(f"[DEBUG] Retrieved ERPPositionId: {erp_position_id}")
        frappe.log(f"[DEBUG] Retrieved PositionName: {position_name}")
        frappe.log(f"[DEBUG] Retrieved Active: {active}")

        # Input Validation: ERPPositionId and PositionName are required.
        if not erp_position_id or not position_name:
            frappe.throw("ERPPositionId and PositionName are required fields.")

        frappe.log(f"[INFO] Sync triggered for Position {erp_position_id} - {position_name}")

        # Construct payload for the API request based on field mappings.
        # Note: OID is auto-increment in the .NET table and is not sent.
        payload = {
            "PositionName": position_name,
            "Active": active,
            "ERPPositionId": erp_position_id
        }

        frappe.log(f"[DEBUG] Constructed Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        # Authenticate to obtain the token
        token = authenticate_xaf()
        frappe.log(f"[INFO] Obtained Token: {token}")

        # Base URL and Endpoints
        base_url = "http://192.168.8.3/hrmwa"
        position_endpoint = f"{base_url}/api/odata/Position"

        # URL-encode the ERPPositionId for safe usage in the filter query
        erp_position_id_encoded = quote(str(erp_position_id))

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

        # Check if the position exists by sending a GET request using a filter query.
        # This query searches for records where ERPPositionId equals the given value.
        check_position_url = f"{position_endpoint}?$filter=ERPPositionId eq '{erp_position_id_encoded}'"
        frappe.log(f"[DEBUG] Sending GET request to: {check_position_url}")
        frappe.log(f"[DEBUG] Headers: {json.dumps(common_headers, indent=2)}")
        check_response = session.get(check_position_url, headers=common_headers, timeout=30)
        frappe.log(f"[DEBUG] Check Position Response: {check_response.status_code} - {check_response.text}")

        if check_response.status_code == 200:
            data = check_response.json()
            # If a record is found, assume the first record is the matching one.
            if data.get("value") and len(data["value"]) > 0:
                # Extract the auto-incremented primary key (OID) for update.
                oid = data["value"][0].get("OID")
                if not oid:
                    frappe.throw("Existing position record found, but primary key (OID) is missing.")
                update_url = f"{position_endpoint}({oid})"
                response = session.patch(
                    update_url,
                    json=payload,
                    headers=common_headers,
                    timeout=30
                )
                frappe.log(f"[INFO] Position exists, updated with PATCH: {response.status_code} - {response.text}")
            else:
                # No matching record; create a new one.
                response = session.post(
                    position_endpoint,
                    json=payload,
                    headers=common_headers,
                    timeout=30
                )
                frappe.log(f"[INFO] Position does not exist, created with POST: {response.status_code} - {response.text}")
        else:
            frappe.throw(f"Error checking position existence: {check_response.status_code} - {check_response.text}")

        frappe.log(f"[DEBUG] Response Status Code: {response.status_code}")
        frappe.log(f"[DEBUG] Response Headers: {response.headers}")
        frappe.log(f"[DEBUG] Response Text: {response.text}")

        response.raise_for_status()
        frappe.log(f"[INFO] Sync successful for Position {erp_position_id}")

    except Exception as e:
        error_response = response.text if response and hasattr(response, 'text') else 'N/A'
        frappe.log_error(
            title="Position Sync Error",
            message=f"Error: {str(e)}\nPayload: {json.dumps(payload, indent=2)}\nResponse: {error_response}"
        )
        frappe.throw(f"Position Sync Error: {str(e)}")

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
