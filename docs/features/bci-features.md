# BCI Features

This document outlines the key features of the Brain-Computer Interface (BCI) component of the BCI-MCP system.

## Supported Devices

The BCI-MCP system is designed to work with a variety of BCI hardware devices, including:

### OpenBCI

- **Cyton Board**: 8-channel EEG acquisition
- **Ganglion Board**: 4-channel EEG acquisition
- **Cyton + Daisy**: 16-channel EEG acquisition
- **WiFi Shield**: Wireless data transmission

### Emotiv

- **EPOC+**: 14-channel EEG headset
- **EPOC Flex**: Advanced EEG acquisition with flexible positioning
- **Insight**: 5-channel mobile EEG headset

### NeuroSky

- **MindWave**: Single-channel EEG headset

### Custom Hardware

- Support for custom and DIY EEG hardware through configurable device interfaces

## Data Acquisition

### Sampling Capabilities

- Adjustable sampling rates (up to 1000 Hz depending on hardware)
- Multi-channel data acquisition
- Real-time impedance checking
- Signal quality monitoring

### Data Formats

- Standard EDF/EDF+ format support
- CSV export functionality
- Integration with common EEG data formats
- Raw data access for custom processing

## EEG Monitoring

### Real-time Visualization

- Time-domain signal plotting
- Frequency spectrum analysis
- Topographical mapping
- Custom visualization components

### Impedance Testing

- Real-time electrode impedance monitoring
- Visual feedback for connection quality
- Electrode status indicators

## Supported Paradigms

### P300

- Oddball paradigm implementation
- P300 speller matrix
- Target detection

### Steady-State Visual Evoked Potentials (SSVEP)

- Frequency-coded stimulation
- Phase-coded stimulation
- Multi-target detection

### Motor Imagery

- Left/right hand imagery
- Multiple body part classification
- Continuous control paradigms

### Passive BCI

- Cognitive workload monitoring
- Attention level tracking
- Emotional state detection

## Markers and Events

### Event Annotation

- Precise timestamp synchronization
- Custom event markers
- Experimental protocol design tools

### Trigger I/O

- External trigger input/output
- Hardware synchronization
- Integration with stimulus presentation software

## Extension Capabilities

### Plugin Architecture

- Custom signal processing plugin support
- Protocol extension framework
- Device driver extensibility

### API Access

- Comprehensive Python API
- WebSocket streaming for web applications
- Network data transmission

## Example Usage

```python
from bci_mcp.devices import OpenBciDevice
from bci_mcp.visualization import SignalViewer

# Connect to an OpenBCI Cyton board
device = OpenBciDevice(port="/dev/ttyUSB0", board_type="cyton")
device.connect()

# Start data streaming
device.start_stream()

# Create a real-time signal viewer
viewer = SignalViewer(device)
viewer.show()

# Add an event marker
device.add_marker(code=1, description="Stimulus onset")

# Access raw data
data = device.get_data(seconds=10)

# Stop streaming when done
device.stop_stream()
device.disconnect()
```

## Next Steps

To understand how these BCI features integrate with the Model Context Protocol, see the [MCP Integration](mcp-integration.md) documentation.