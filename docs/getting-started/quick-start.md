# Quick Start Guide

This guide will help you get started with BCI-MCP quickly. We'll walk through installation, basic configuration, and running your first BCI session with MCP integration.

## Prerequisites

Before you begin, make sure you have:

- Python 3.10 or newer
- Compatible EEG hardware (or use simulated mode for testing)
- Basic understanding of terminal/command line usage

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/enkhbold470/bci-mcp.git
cd bci-mcp
```

### 2. Create a Virtual Environment

We recommend using a virtual environment to avoid conflicts with other Python packages:

```bash
# Using venv
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Basic Usage

### Running in Interactive Mode

The simplest way to start is with the interactive console mode:

```bash
python src/main.py --interactive
```

This will display a menu-driven interface for:
- Selecting your EEG device
- Calibrating the system
- Starting/stopping data streaming
- Recording and analyzing sessions

### List Available EEG Devices

To see which EEG devices are connected to your system:

```bash
python src/main.py --list-ports
```

The output will show available serial ports and connected devices.

### Recording a BCI Session

To record a 60-second BCI session:

```bash
python src/main.py --port /dev/tty.usbmodem1101 --record 60
```

Replace `/dev/tty.usbmodem1101` with your device's port as shown in the `--list-ports` output.

### Calibration

For optimal performance, calibrate the system before a session:

```bash
python src/main.py --port /dev/tty.usbmodem1101 --calibrate
```

## Starting the MCP Server

To expose your BCI functionality through the Model Context Protocol:

```bash
python src/main.py --server
```

By default, this starts an MCP server on `ws://localhost:8765`.

## Connecting to the MCP Server

### Using Python

Here's a simple example of connecting to the MCP server using Python:

```python
import asyncio
import json
from websockets import connect

async def use_bci_mcp():
    async with connect("ws://localhost:8765") as websocket:
        # Get capabilities
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "method": "get_capabilities",
            "id": 1
        }))
        response = await websocket.recv()
        print(f"Capabilities: {json.loads(response)}")
        
        # Connect to a device
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "method": "invoke_tool_connect_device",
            "params": {"port": "/dev/tty.usbmodem1101"},
            "id": 2
        }))
        response = await websocket.recv()
        print(f"Connection result: {json.loads(response)}")
        
        # Start streaming
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "method": "invoke_tool_start_stream",
            "id": 3
        }))
        response = await websocket.recv()
        print(f"Streaming result: {json.loads(response)}")
        
        # Read brain signals
        for _ in range(5):  # Get 5 samples
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "get_resource_brain_signals",
                "id": 4
            }))
            response = await websocket.recv()
            print(f"Brain signals: {json.loads(response)}")
            await asyncio.sleep(1)
        
        # Stop streaming
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "method": "invoke_tool_stop_stream",
            "id": 5
        }))
        response = await websocket.recv()
        print(f"Stop result: {json.loads(response)}")

asyncio.run(use_bci_mcp())
```

### Using Other Languages

The MCP protocol uses standard WebSockets and JSON-RPC 2.0, so you can connect using any language that supports these technologies. See the [MCP specification](https://spec.modelcontextprotocol.io/) for detailed protocol information.

## Common Operations

Here are some common operations you might want to perform:

### Calibrate the Device

```python
await websocket.send(json.dumps({
    "jsonrpc": "2.0",
    "method": "invoke_tool_calibrate_device",
    "params": {"duration": 10},
    "id": 10
}))
```

### Save Session Data

```python
await websocket.send(json.dumps({
    "jsonrpc": "2.0",
    "method": "invoke_tool_save_data",
    "params": {"format": "npz"},
    "id": 11
}))
```

### Get Session Information

```python
await websocket.send(json.dumps({
    "jsonrpc": "2.0",
    "method": "get_resource_session_info",
    "id": 12
}))
```

## Next Steps

Now that you have BCI-MCP up and running, you might want to:

1. Learn about [advanced BCI features](../features/bci-features.md)
2. Explore the [MCP integration](../features/mcp-integration.md) in more detail
3. Check the [API reference](../api/bci-module.md) for programmatic usage

If you encounter any issues, please check the troubleshooting section or submit an issue on our GitHub repository.