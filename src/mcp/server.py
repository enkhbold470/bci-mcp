"""
Model Context Protocol (MCP) server implementation for BCI.
Exposes brain interface functionality via the MCP protocol.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from jsonrpcserver import method, Success, Error, async_dispatch
import websockets

from ..bci.brain_interface import BrainInterface, list_serial_ports

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bci-mcp-server")

# Global BCI instance
brain_interface = None

# Store session data for MCP resources
session_data = {
    "device_connected": False,
    "streaming": False,
    "events": [],
    "event_count": 0,
    "session_start": None,
    "calibration": {}
}

# Capability descriptions for MCP
SERVER_CAPABILITIES = {
    "name": "BCI-MCP Server",
    "version": "0.1.0",
    "description": "Brain-Computer Interface server implementing the Model Context Protocol",
    "resources": {
        "brain_signals": {
            "description": "Access to real-time brain signal data and detected events"
        },
        "session_info": {
            "description": "Information about the current BCI session"
        },
        "device_info": {
            "description": "Information about the connected BCI device"
        }
    },
    "tools": {
        "connect_device": {
            "description": "Connect to a BCI device"
        },
        "disconnect_device": {
            "description": "Disconnect from the BCI device"
        },
        "start_stream": {
            "description": "Start streaming data from the connected device"
        },
        "stop_stream": {
            "description": "Stop streaming data from the connected device"
        },
        "calibrate_device": {
            "description": "Calibrate the BCI device for optimal performance"
        },
        "save_data": {
            "description": "Save the current session data"
        },
        "list_available_devices": {
            "description": "List available BCI devices"
        }
    }
}

@method
async def get_capabilities():
    """Return server capabilities for MCP negotiation"""
    return Success(SERVER_CAPABILITIES)

@method
async def initialize(client_capabilities: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize MCP connection with client"""
    logger.info(f"Client connected with capabilities: {client_capabilities}")
    return Success({
        "server_info": {
            "name": SERVER_CAPABILITIES["name"],
            "version": SERVER_CAPABILITIES["version"],
            "status": "ready"
        }
    })

# Resource methods

@method
async def get_resource_brain_signals() -> Dict[str, Any]:
    """Resource method to access brain signals and events"""
    global brain_interface, session_data
    
    if not brain_interface or not session_data["streaming"]:
        return Success({
            "status": "not_streaming",
            "message": "Brain interface is not streaming data"
        })
    
    # Get the latest signal data
    if brain_interface.current_sample_idx < 250:  # Less than 1 second of data
        indices = range(0, brain_interface.current_sample_idx)
        if len(indices) == 0:
            return Success({
                "status": "no_data",
                "message": "No data has been collected yet"
            })
    else:
        # Get the most recent 1 second of data
        current_pos = brain_interface.current_sample_idx % brain_interface.BUFFER_SIZE
        indices = [(current_pos - i) % brain_interface.BUFFER_SIZE for i in range(250)]
    
    # Extract data
    raw_data = brain_interface.raw_buffer[0, indices].tolist()
    filtered_data = brain_interface.filtered_buffer[0, indices].tolist()
    timestamps = (brain_interface.timestamps[indices] - brain_interface.start_time).tolist()
    
    # Format recent events (last 5)
    recent_events = []
    if session_data["events"]:
        for i in range(min(5, len(session_data["events"]))):
            recent_events.append(session_data["events"][-(i+1)])
    
    return Success({
        "status": "streaming",
        "sample_rate": 250,
        "channels": brain_interface.channels,
        "data": {
            "timestamps": timestamps,
            "raw": raw_data,
            "filtered": filtered_data,
        },
        "events": {
            "count": session_data["event_count"],
            "recent": recent_events
        }
    })

@method
async def get_resource_session_info() -> Dict[str, Any]:
    """Resource method to access session information"""
    global brain_interface, session_data
    
    if not brain_interface:
        return Success({
            "status": "no_device",
            "message": "No brain interface has been initialized"
        })
    
    # Calculate session duration
    session_duration = 0
    if session_data["session_start"]:
        session_duration = time.time() - session_data["session_start"]
    
    return Success({
        "device_connected": session_data["device_connected"],
        "streaming": session_data["streaming"],
        "event_count": session_data["event_count"],
        "duration": session_duration,
        "start_time": session_data["session_start"],
        "calibration_status": "completed" if session_data["calibration"] else "not_calibrated"
    })

@method
async def get_resource_device_info() -> Dict[str, Any]:
    """Resource method to access device information"""
    global brain_interface
    
    if not brain_interface:
        return Success({
            "status": "no_device",
            "message": "No brain interface has been initialized"
        })
    
    return Success({
        "connected": brain_interface.running,
        "port": brain_interface.port,
        "device_type": brain_interface.device_type,
        "channels": brain_interface.channels,
        "sample_rate": 250,
        "detection_threshold": brain_interface.detection_threshold,
        "cooldown_period": brain_interface.cooldown_period
    })

# Tool methods

@method
async def invoke_tool_connect_device(port: Optional[str] = None) -> Dict[str, Any]:
    """Tool method to connect to a BCI device"""
    global brain_interface, session_data
    
    # Initialize the interface if needed
    if not brain_interface:
        brain_interface = BrainInterface(port=port)
        # Register event callback
        brain_interface.register_event_callback(on_neural_event)
    elif port:
        brain_interface.port = port
    
    # Connect to the device
    success = brain_interface.connect()
    session_data["device_connected"] = success
    
    if success:
        return Success({
            "status": "connected",
            "port": brain_interface.port,
            "message": f"Successfully connected to device on {brain_interface.port}"
        })
    else:
        return Error(
            code=-32000, 
            message=f"Failed to connect to device on {brain_interface.port or 'unknown port'}"
        )

@method
async def invoke_tool_disconnect_device() -> Dict[str, Any]:
    """Tool method to disconnect from the BCI device"""
    global brain_interface, session_data
    
    if not brain_interface:
        return Error(code=-32001, message="No device has been initialized")
    
    if not session_data["device_connected"]:
        return Error(code=-32002, message="No device is currently connected")
    
    # Disconnect from the device
    brain_interface.disconnect()
    session_data["device_connected"] = False
    session_data["streaming"] = False
    
    return Success({
        "status": "disconnected",
        "message": "Successfully disconnected from device"
    })

@method
async def invoke_tool_start_stream() -> Dict[str, Any]:
    """Tool method to start streaming data from the device"""
    global brain_interface, session_data
    
    if not brain_interface:
        return Error(code=-32001, message="No device has been initialized")
    
    if not session_data["device_connected"]:
        return Error(code=-32002, message="No device is currently connected")
    
    if session_data["streaming"]:
        return Success({
            "status": "already_streaming",
            "message": "Device is already streaming"
        })
    
    # Start streaming
    success = brain_interface.start_stream()
    if success:
        session_data["streaming"] = True
        session_data["session_start"] = time.time()
        session_data["events"] = []
        session_data["event_count"] = 0
        
        return Success({
            "status": "streaming",
            "message": "Successfully started streaming data"
        })
    else:
        return Error(code=-32003, message="Failed to start streaming")

@method
async def invoke_tool_stop_stream() -> Dict[str, Any]:
    """Tool method to stop streaming data from the device"""
    global brain_interface, session_data
    
    if not brain_interface:
        return Error(code=-32001, message="No device has been initialized")
    
    if not session_data["streaming"]:
        return Success({
            "status": "not_streaming",
            "message": "Device is not currently streaming"
        })
    
    # Stop streaming
    brain_interface.stop_stream()
    session_data["streaming"] = False
    
    return Success({
        "status": "stopped",
        "message": "Successfully stopped streaming data",
        "session_summary": {
            "duration": time.time() - session_data["session_start"],
            "event_count": session_data["event_count"]
        }
    })

@method
async def invoke_tool_calibrate_device(duration: int = 10) -> Dict[str, Any]:
    """Tool method to calibrate the BCI device"""
    global brain_interface, session_data
    
    if not brain_interface:
        return Error(code=-32001, message="No device has been initialized")
    
    if not session_data["device_connected"]:
        return Error(code=-32002, message="No device is currently connected")
    
    # Perform calibration
    was_streaming = session_data["streaming"]
    
    brain_interface.calibrate(duration=duration)
    
    # Store calibration data
    session_data["calibration"] = {
        "timestamp": time.time(),
        "duration": duration,
        "threshold": brain_interface.detection_threshold
    }
    
    # Reset streaming state if needed
    session_data["streaming"] = brain_interface.streaming
    
    return Success({
        "status": "calibrated",
        "message": f"Device calibrated over {duration} seconds",
        "threshold": brain_interface.detection_threshold,
        "streaming_state": "continued" if was_streaming and session_data["streaming"] else "stopped"
    })

@method
async def invoke_tool_save_data(format: str = "npz") -> Dict[str, Any]:
    """Tool method to save the current session data"""
    global brain_interface, session_data
    
    if not brain_interface:
        return Error(code=-32001, message="No device has been initialized")
    
    if brain_interface.current_sample_idx == 0:
        return Error(code=-32004, message="No data to save")
    
    # Save the data
    filename = brain_interface.save_data(format=format)
    
    if filename:
        return Success({
            "status": "saved",
            "message": f"Data saved to {filename}",
            "path": filename,
            "format": format
        })
    else:
        return Error(code=-32005, message=f"Failed to save data in format {format}")

@method
async def invoke_tool_list_available_devices() -> Dict[str, Any]:
    """Tool method to list available BCI devices"""
    ports = list_serial_ports()
    
    return Success({
        "devices": [{"index": i, "port": port} for i, port in enumerate(ports)],
        "count": len(ports)
    })

async def on_neural_event(event_count, elapsed_time):
    """Callback function for neural events"""
    global session_data
    
    # Create event record
    event = {
        "id": event_count,
        "timestamp": time.time(),
        "elapsed_time": elapsed_time
    }
    
    # Update session data
    session_data["events"].append(event)
    session_data["event_count"] = event_count
    
    # Log the event
    logger.info(f"Neural event detected: #{event_count} at {elapsed_time:.2f}s")

async def handle_connection(websocket, path):
    """Handle WebSocket connections"""
    logger.info(f"Client connected from {websocket.remote_address}")
    
    try:
        async for message in websocket:
            # Parse and dispatch JSON-RPC message
            try:
                response = await async_dispatch(message)
                if response:
                    await websocket.send(response)
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                error_response = json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None})
                await websocket.send(error_response)
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {websocket.remote_address}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

async def start_server(host='0.0.0.0', port=8765):
    """Start the MCP WebSocket server"""
    server = await websockets.serve(handle_connection, host, port)
    logger.info(f"BCI-MCP Server running at ws://{host}:{port}")
    
    # Create global BCI instance
    global brain_interface
    brain_interface = BrainInterface()
    
    # Keep the server running
    await server.wait_closed()

def run_server():
    """Run the MCP server"""
    # Create recordings directory if it doesn't exist
    os.makedirs("recordings", exist_ok=True)
    
    # Start server
    logger.info("Starting BCI-MCP Server...")
    asyncio.run(start_server())

if __name__ == "__main__":
    run_server()