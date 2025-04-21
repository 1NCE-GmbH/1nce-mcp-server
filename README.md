# 1NCE IoT Platform MCP Server

A Model Context Protocol (MCP) server that enables AI agents to interact with the 1NCE IoT connectivity management platform through natural language.

## Overview

This project provides a middleware layer that connects Large Language Models (LLMs) to the 1NCE API for managing IoT connectivity. It allows AI assistants to:

- Retrieve product information
- Manage orders
- Monitor SIM card status
- Check data and SMS quotas
- Update SIM configurations
- View connectivity information

By exposing these capabilities through the Model Context Protocol, AI agents can interact with IoT infrastructure using natural language, simplifying the management of connected devices.

## Features

- **Authentication**: Secure OAuth 2.0 token-based authentication with 1NCE API
- **Product Management**: Query available IoT connectivity products
- **Order Management**: Create and track orders
- **SIM Management**: Monitor and configure SIM cards
- **Resources**: Direct access to SIM status and product data
- **Prompts**: Pre-defined interaction templates for common tasks

## Prerequisites

- Python 3.8+
- FastMCP v2
- 1NCE account with API credentials

## Installation

1. Clone this repository
```bash
git clone https://github.com/yourusername/1nce-mcp-server.git
cd 1nce-mcp-server
```

2. Install required dependencies
```bash
pip install fastmcp httpx
```

3. Set environment variables with your 1NCE API credentials
```bash
export ONCE_CLIENT_ID="your_client_id"
export ONCE_CLIENT_SECRET="your_client_secret"
```

## Usage

### Installing with FastMCP

The recommended way to use this MCP server is to install it using the FastMCP CLI:

```bash
fastmcp install 1nce_mcp.py
```

This will make the server available to compatible MCP clients, including Claude Desktop.

### Running Directly

For development or testing, you can run the server directly:

```bash
python 1nce_mcp.py
```

### Using with a Client

You can interact with the server programmatically using the FastMCP client:

```python
from fastmcp import Client

async with Client("1nce_mcp.py") as client:
    # Get list of products
    products = await client.call_tool("get_all_products")
    print(products)
    
    # Check SIM status
    sim_status = await client.call_tool("get_sim_status", {"iccid": "your_sim_iccid"})
    print(sim_status)
```

## Available Tools

### Product Tools
- `get_all_products()` - Retrieve all available 1NCE products

### Order Tools
- `get_all_orders(page, page_size, sort)` - Get list of orders with pagination
- `get_order_by_number(order_number)` - Get details of a specific order
- `create_order(products, delivery_address, customer_reference)` - Create a new order

### SIM Tools
- `get_all_sims(page, page_size, query, sort)` - List SIM cards with filtering options
- `get_sim_details(iccid)` - Get detailed information about a specific SIM
- `get_sim_status(iccid)` - Check the connectivity status of a SIM
- `get_sim_data_quota(iccid)` - Check remaining data quota for a SIM
- `get_sim_sms_quota(iccid)` - Check remaining SMS quota for a SIM
- `update_sim_status(iccid, status, label, imei_lock)` - Update SIM configuration
- `get_sim_usage(iccid, start_date, end_date)` - Get usage statistics for a time period
- `get_sim_events(iccid, page, page_size, sort)` - Get event history for a SIM
- `reset_sim_connectivity(iccid)` - Trigger a connectivity reset for a SIM

## Examples

### Checking SIM Status

```python
from fastmcp import Client

async with Client("1nce_mcp.py") as client:
    # Check SIM status
    sim_status = await client.call_tool("get_sim_status", {
        "iccid": "8988303000123456789"
    })
    print(f"SIM Status: {sim_status.get('status')}")
    
    # Check data quota
    quota = await client.call_tool("get_sim_data_quota", {
        "iccid": "8988303000123456789"
    })
    print(f"Remaining data: {quota.get('volume')} MB")
    print(f"Expires on: {quota.get('expiry_date')}")
```

### Creating an Order

```python
from fastmcp import Client

async with Client("1nce_mcp.py") as client:
    # Create an order for 5 SIM cards
    order = await client.call_tool("create_order", {
        "products": [{"productId": 1001, "quantity": 5}],
        "customer_reference": "IoT-Project-XYZ"
    })
    print(f"Order created with number: {order.get('order_number')}")
```

## Security

- The MCP server requires 1NCE API credentials to be set as environment variables
- Authentication is performed using OAuth 2.0 with Basic Authentication
- Access tokens are obtained dynamically and not stored persistently
- The server only exposes necessary API operations, prioritizing read operations over write operations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [1NCE](https://1nce.com/) for providing the IoT connectivity API
- [FastMCP](https://gofastmcp.com/) for the MCP server framework
- [Anthropic](https://www.anthropic.com/) for Claude AI assistant capabilities