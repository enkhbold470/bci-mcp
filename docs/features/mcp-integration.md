# MCP Integration

The Model Context Protocol (MCP) integration is a key feature of our BCI system, allowing seamless connection between neural data and AI applications. This page details how our implementation combines brain-computer interfacing with the standardized AI communication protocol.

## What is MCP?

The Model Context Protocol (MCP) is an open standard developed by Anthropic that enables secure, two-way connections between AI systems and various data sources. It provides a standardized way for:

- Sharing contextual information with language models
- Exposing tools and capabilities to AI systems
- Building composable integrations and workflows

## BCI-MCP Architecture

Our integration connects BCI technology with MCP through a modular architecture:

```
┌────────────┐      ┌───────────────┐      ┌─────────────┐      ┌───────────────┐
│            │      │               │      │             │      │               │
│ EEG Device │─────▶│ BCI Interface │─────▶│ MCP Server │─────▶│ AI Applications│
│            │      │               │      │             │      │               │
└────────────┘      └───────────────┘      └─────────────┘      └───────────────┘
```

### Key Components

1. **BCI Interface**: Handles neural signal acquisition and processing
2. **MCP Server**: Exposes BCI capabilities via standardized JSON-RPC protocol
3. **WebSocket Transport**: Provides real-time communication
4. **Client Connections**: Allows multiple AI applications to access BCI functionality

## MCP Resources

Our implementation exposes several resources through the MCP protocol:

### 1. Brain Signals Resource

Provides access to real-time neural data:

```json
{
  "status": "streaming",
  "sample_rate": 250,
  "channels": 1,
  "data": {
    "timestamps": [0.001, 0.005, ...],
    "raw": [10243, 10250, ...],
    "filtered": [0.5, 0.7, ...]
  },
  "events": {
    "count": 5,
    "recent": [
      {"id": 5, "timestamp": 1648372591.23, "elapsed_time": 45.7}
    ]
  }
}
```

### 2. Session Info Resource

Provides information about the current BCI session:

```json
{
  "device_connected": true,
  "streaming": true,
  "event_count": 12,
  "duration": 120.5,
  "start_time": 1648372545.73,
  "calibration_status": "completed"
}
```

### 3. Device Info Resource

Provides details about the connected BCI hardware:

```json
{
  "connected": true,
  "port": "/dev/tty.usbmodem1101",
  "device_type": "BCI_MCP_Device",
  "channels": 1,
  "sample_rate": 250,
  "detection_threshold": 5.0,
  "cooldown_period": 0.5
}
```

## MCP Tools

The BCI-MCP server exposes several tools that AI applications can use:

### Device Control Tools

- **connect_device**: Connect to a BCI device
- **disconnect_device**: Disconnect from the BCI device
- **list_available_devices**: List available BCI devices

### Stream Management Tools

- **start_stream**: Start streaming data from the connected device
- **stop_stream**: Stop streaming data from the connected device
- **calibrate_device**: Calibrate the BCI device for optimal performance
- **save_data**: Save the current session data

## Integration Benefits

The BCI-MCP integration offers several advantages:

### 1. Standardized Access

- Consistent API for accessing neural data
- Language-agnostic protocol
- Easy integration with AI systems

### 2. Enhanced Capabilities

- AI-assisted signal interpretation
- Contextual understanding of neural patterns
- Advanced command mapping

### 3. Security and Privacy

- Controlled access to neural data
- Structured permission system
- Data minimization capabilities

### 4. Extensibility

- Support for new BCI features without protocol changes
- Versioned capability negotiation
- Backward compatibility

## Example Workflows

The BCI-MCP integration enables sophisticated workflows:

### Assistive Communication

1. BCI detects neural patterns associated with intended speech
2. MCP server provides this data to an AI assistant
3. AI interprets the patterns in context of previous communication
4. AI generates appropriate responses or actions

### Adaptive Interfaces

1. BCI continuously monitors user's cognitive state
2. MCP server streams this data to UI management system
3. AI adjusts interface complexity based on cognitive load
4. Interface elements adapt in real-time to user's state

### Neural Biofeedback

1. BCI processes specific frequency bands in neural data
2. MCP server provides this data to an AI coach
3. AI analyzes patterns and provides personalized guidance
4. User receives feedback to improve neural control

## Getting Started with BCI-MCP

To start using the MCP integration with BCI:

1. Install the BCI-MCP package following our [installation guide](../getting-started/installation.md)
2. Start the MCP server with `python src/main.py --server`
3. Connect AI applications to the server via WebSocket at `ws://localhost:8765`
4. Use standard MCP protocol methods to access BCI functionality

For more detailed examples, see our [Quick Start Guide](../getting-started/quick-start.md).