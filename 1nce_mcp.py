"""
1NCE IoT Platform MCP Server

This MCP (Model Context Protocol) server provides a middleware layer between
LLMs and the 1NCE IoT connectivity management API. It enables AI agents to
interact with SIM cards, products, and orders through natural language.

Author: Jan Sulaiman
"""

from fastmcp import FastMCP
import httpx
import os
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime

# ------------------------------------------------------------------------------
# MCP Server Configuration
# ------------------------------------------------------------------------------

# Initialize the MCP server with a friendly name and dependencies
mcp = FastMCP("1NCE IoT Platform MCP", dependencies=["httpx"])

# Environment Variables
ONCE_CLIENT_ID = os.environ.get("ONCE_CLIENT_ID")
ONCE_CLIENT_SECRET = os.environ.get("ONCE_CLIENT_SECRET")
ONCE_API_URL = "https://api.1nce.com/management-api"

if not ONCE_CLIENT_ID or not ONCE_CLIENT_SECRET:
    raise ValueError("Environment variables ONCE_CLIENT_ID and ONCE_CLIENT_SECRET must be set.")

# ------------------------------------------------------------------------------
# Authentication
# ------------------------------------------------------------------------------

async def get_oauth_token() -> str:
    """Fetches an OAuth 2.0 access token from the 1NCE API."""
    # Create Basic Authentication header with client_id:client_secret
    auth_string = f"{ONCE_CLIENT_ID}:{ONCE_CLIENT_SECRET}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ONCE_API_URL}/oauth/token",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Basic {auth_b64}",
            },
            json={
                "grant_type": "client_credentials"
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("access_token")

# ------------------------------------------------------------------------------
# Product API Tools
# ------------------------------------------------------------------------------

@mcp.tool()
async def get_all_products():
    """
    Retrieve all available 1NCE products and their details.
    
    Returns a list of available IoT connectivity products 
    with their pricing details, package sizes, and specifications.
    """
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/products",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

# ------------------------------------------------------------------------------
# Order API Tools
# ------------------------------------------------------------------------------

@mcp.tool()
async def get_all_orders(page: int = 1, page_size: int = 10, sort: str = "order_number"):
    """
    Retrieve all orders for the current account with pagination.
    
    Parameters:
    - page: Page number to retrieve (starts at 1)
    - page_size: Number of orders per page (max 10)
    - sort: Sort order, comma-separated list (e.g., "order_status,order_date")
    
    Returns a list of orders with their details including order status,
    products ordered, and delivery information.
    """
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/orders",
            params={
                "page": page,
                "pageSize": min(page_size, 10),  # Ensure we don't exceed max allowed
                "sort": sort
            },
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_order_by_number(order_number: int):
    """
    Retrieve details of a specific order by its order number.
    
    Parameters:
    - order_number: The unique order number to retrieve
    
    Returns detailed information about the specified order including 
    products, quantities, shipping address, and status.
    """
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/orders/{order_number}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def create_order(products: List[Dict[str, Any]], delivery_address: Optional[Dict[str, Any]] = None, customer_reference: Optional[str] = None):
    """
    Create a new order for 1NCE products.
    
    Parameters:
    - products: List of products to order, each with productId and quantity
      Example: [{"productId": 1001, "quantity": 5}]
    - delivery_address: Optional shipping address details
    - customer_reference: Optional reference identifier for this order
    
    Returns the created order details including order number and status.
    """
    access_token = await get_oauth_token()
    
    # Prepare request body
    request_body = {
        "products": products
    }
    
    if delivery_address:
        request_body["delivery_address"] = delivery_address
    
    if customer_reference:
        request_body["customer_reference"] = customer_reference
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ONCE_API_URL}/v1/orders",
            json=request_body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

# ------------------------------------------------------------------------------
# SIM API Tools
# ------------------------------------------------------------------------------

@mcp.tool()
async def get_all_sims(page: int = 1, page_size: int = 10, query: Optional[str] = None, sort: Optional[str] = None):
    """
    Retrieve a list of all SIMs for the current account with pagination and filtering.
    
    Parameters:
    - page: Page number to retrieve (starts at 1)
    - page_size: Number of SIMs per page (max 100)
    - query: Optional filter in format "field:value,field:value" 
      Example: "imei:12345,ip_address:10.0.0.1"
    - sort: Optional sort order, comma-separated list 
      Example: "ip_address,-imei"
    
    Returns a list of SIM cards with their details including status,
    IP address, and activation information.
    """
    access_token = await get_oauth_token()
    
    params = {
        "page": page,
        "pageSize": min(page_size, 100),  # Ensure we don't exceed max allowed
    }
    
    if query:
        params["q"] = query
    
    if sort:
        params["sort"] = sort
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/sims",
            params=params,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_sim_details(iccid: str):
    """
    Retrieve detailed information about a specific SIM by its ICCID.
    
    Parameters:
    - iccid: The ICCID of the SIM to query
    
    Returns detailed information about the SIM including activation status,
    IP address, quota information, and more.
    """
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/sims/{iccid}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_sim_status(iccid: str):
    """
    Get the current connection status of a specific SIM.
    
    Parameters:
    - iccid: The ICCID of the SIM to query
    
    Returns the connectivity status including whether the SIM is online,
    attached, or offline, and current network information.
    """
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/sims/{iccid}/status",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_sim_data_quota(iccid: str):
    """
    Retrieve the data quota for a given SIM ICCID.
    
    Parameters:
    - iccid: The ICCID of the SIM to query
    
    Returns the current data quota information including total volume,
    remaining volume, and expiration date.
    """
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/sims/{iccid}/quota/data",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_sim_sms_quota(iccid: str):
    """
    Retrieve the SMS quota for a given SIM ICCID.
    
    Parameters:
    - iccid: The ICCID of the SIM to query
    
    Returns the current SMS quota information including total SMS count,
    remaining SMS count, and expiration date.
    """
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/sims/{iccid}/quota/sms",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def update_sim_status(iccid: str, status: str, label: Optional[str] = None, imei_lock: Optional[bool] = None):
    """
    Update a SIM's status, label, or IMEI lock setting.
    
    Parameters:
    - iccid: The ICCID of the SIM to update
    - status: New status for the SIM ("Enabled" or "Disabled")
    - label: Optional new label for the SIM
    - imei_lock: Optional boolean to enable/disable IMEI locking
    
    Returns a confirmation of the update operation.
    """
    if status not in ["Enabled", "Disabled"]:
        return {"error": "Status must be either 'Enabled' or 'Disabled'"}
    
    access_token = await get_oauth_token()
    
    # Prepare update data
    update_data = {
        "iccid": iccid,
        "status": status
    }
    
    if label is not None:
        update_data["label"] = label
    
    if imei_lock is not None:
        update_data["imei_lock"] = imei_lock
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{ONCE_API_URL}/v1/sims/{iccid}",
            json=update_data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return {"success": True, "message": f"SIM {iccid} updated successfully"}

@mcp.tool()
async def get_sim_usage(iccid: str, start_date: str, end_date: str):
    """
    Retrieve usage information for a specific SIM over a time period.
    
    Parameters:
    - iccid: The ICCID of the SIM to query
    - start_date: Start date in YYYY-MM-DD format
    - end_date: End date in YYYY-MM-DD format
    
    Returns daily usage statistics for the specified date range.
    """
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Dates must be in YYYY-MM-DD format"}
    
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/sims/{iccid}/usage",
            params={
                "start_dt": start_date,
                "end_dt": end_date
            },
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()



@mcp.tool()
async def get_sim_events(iccid: str, page: int = 1, page_size: int = 10, sort: str = "-timestamp"):
    """
    Retrieve event information for a specific SIM.
    
    Parameters:
    - iccid: The ICCID of the SIM to query
    - page: Page number to retrieve (starts at 1)
    - page_size: Number of events per page (max 1000)
    - sort: Sort order (default: "-timestamp" shows newest events first)
    
    Returns a list of events for the specified SIM, such as status changes,
    connections, and other activities.
    """
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/sims/{iccid}/events",
            params={
                "page": page,
                "pageSize": min(page_size, 1000),  # Ensure we don't exceed max allowed
                "sort": sort
            },
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def reset_sim_connectivity(iccid: str):
    """
    Trigger a connectivity reset for a specific SIM.
    
    Parameters:
    - iccid: The ICCID of the SIM to reset
    
    Returns a confirmation of the reset operation.
    """
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ONCE_API_URL}/v1/sims/{iccid}/reset",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return {"success": True, "message": f"Connectivity reset triggered for SIM {iccid}"}



# ------------------------------------------------------------------------------
# MCP Resources
# ------------------------------------------------------------------------------

@mcp.resource("resource://1nce/sims/{iccid}/status")
async def sim_status_resource(iccid: str):
    """Get the current status of a specific SIM."""
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/sims/{iccid}/status",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.resource("resource://1nce/products")
async def products_resource():
    """Get all available 1NCE products."""
    access_token = await get_oauth_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ONCE_API_URL}/v1/products",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return response.json()

# ------------------------------------------------------------------------------
# MCP Prompts
# ------------------------------------------------------------------------------

@mcp.prompt()
def check_sim_status_prompt(iccid: str):
    """Generate a prompt to check the status of a SIM."""
    return f"Please check the status of SIM with ICCID {iccid} and let me know if it's active, what its current data usage is, and when its quota expires."

@mcp.prompt()
def order_status_prompt(order_number: int):
    """Generate a prompt to check the status of an order."""
    return f"Please check the status of order #{order_number} and let me know when it was placed, what products were ordered, and what the current status is."

# ------------------------------------------------------------------------------
# Server Startup
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    mcp.run()