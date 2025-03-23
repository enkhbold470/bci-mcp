# BCI Module API Reference

This document provides a comprehensive reference for the Brain-Computer Interface (BCI) module API.

## Core Classes

### `BciDevice`

Base class for all BCI devices.

```python
class BciDevice:
    def __init__(self, config):
        """
        Initialize a BCI device.
        
        Args:
            config (dict): Configuration parameters for the device
        """
        pass
    
    def connect(self):
        """
        Connect to the BCI device.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    def disconnect(self):
        """
        Disconnect from the BCI device.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass
    
    def start_stream(self):
        """
        Start data streaming from the device.
        
        Returns:
            bool: True if streaming started successfully, False otherwise
        """
        pass
    
    def stop_stream(self):
        """
        Stop data streaming from the device.
        
        Returns:
            bool: True if streaming stopped successfully, False otherwise
        """
        pass
    
    def get_data(self, samples=None):
        """
        Get data from the device buffer.
        
        Args:
            samples (int, optional): Number of samples to retrieve
            
        Returns:
            numpy.ndarray: Array of samples with shape (samples, channels)
        """
        pass
```

### `OpenBciDevice`

Implementation of `BciDevice` for OpenBCI hardware.

```python
class OpenBciDevice(BciDevice):
    def __init__(self, port, baud=115200, board_type="cyton"):
        """
        Initialize an OpenBCI device.
        
        Args:
            port (str): Serial port for the device
            baud (int): Baud rate for serial communication
            board_type (str): Type of OpenBCI board ('cyton', 'ganglion', or 'daisy')
        """
        pass
    
    # Additional OpenBCI-specific methods
    def set_channel_settings(self, channel, setting):
        """
        Configure settings for a specific channel.
        
        Args:
            channel (int): Channel number (1-based)
            setting (str): Setting command
            
        Returns:
            bool: True if setting was applied successfully, False otherwise
        """
        pass
```

### `EmotivDevice`

Implementation of `BciDevice` for Emotiv hardware.

```python
class EmotivDevice(BciDevice):
    def __init__(self, client_id, client_secret, profile=None):
        """
        Initialize an Emotiv device.
        
        Args:
            client_id (str): Emotiv API client ID
            client_secret (str): Emotiv API client secret
            profile (str, optional): User profile name
        """
        pass
    
    # Additional Emotiv-specific methods
    def get_contact_quality(self):
        """
        Get the contact quality for each electrode.
        
        Returns:
            dict: Dictionary mapping electrode names to quality values
        """
        pass
```

## Utility Functions

### Data Handling

```python
def save_recording(data, filename, metadata=None):
    """
    Save recorded BCI data to a file.
    
    Args:
        data (numpy.ndarray): Data array with shape (samples, channels)
        filename (str): Output file name
        metadata (dict, optional): Additional metadata to save
    
    Returns:
        bool: True if save was successful, False otherwise
    """
    pass

def load_recording(filename):
    """
    Load recorded BCI data from a file.
    
    Args:
        filename (str): Input file name
    
    Returns:
        tuple: (data, metadata) where data is a numpy.ndarray
    """
    pass
```

### Device Discovery

```python
def list_available_devices():
    """
    List all available BCI devices connected to the system.
    
    Returns:
        list: List of dictionaries with device information
    """
    pass

def auto_detect_device():
    """
    Automatically detect and connect to a BCI device.
    
    Returns:
        BciDevice: Connected device instance or None if no device found
    """
    pass
```

## Events and Markers

```python
class MarkerHandler:
    def __init__(self, device):
        """
        Initialize a marker handler for event annotation.
        
        Args:
            device (BciDevice): The BCI device to attach to
        """
        pass
    
    def add_marker(self, marker_code, timestamp=None, description=None):
        """
        Add a marker to the data stream.
        
        Args:
            marker_code (int): Numeric code for the marker
            timestamp (float, optional): Custom timestamp (uses current time if None)
            description (str, optional): Text description of the marker
            
        Returns:
            bool: True if marker was added successfully, False otherwise
        """
        pass
    
    def get_markers(self, start_time=None, end_time=None):
        """
        Get markers within a time range.
        
        Args:
            start_time (float, optional): Start time for marker retrieval
            end_time (float, optional): End time for marker retrieval
            
        Returns:
            list: List of markers with timestamps and codes
        """
        pass
```

## Exception Classes

```python
class BciError(Exception):
    """Base exception class for all BCI-related errors."""
    pass

class ConnectionError(BciError):
    """Exception raised when connection to a BCI device fails."""
    pass

class StreamError(BciError):
    """Exception raised when there is an error with the data stream."""
    pass

class ConfigurationError(BciError):
    """Exception raised when there is an error in the device configuration."""
    pass
```

## Usage Examples

```python
# Example 1: Basic usage with OpenBCI
from src.bci import OpenBciDevice

# Initialize the device
device = OpenBciDevice(port="/dev/ttyUSB0", board_type="cyton")

# Connect and start streaming
if device.connect():
    device.start_stream()
    
    # Get 1000 samples of data
    data = device.get_data(samples=1000)
    
    # Process the data
    # ...
    
    # Stop streaming and disconnect
    device.stop_stream()
    device.disconnect()

# Example 2: Using markers for event-related analysis
from src.bci import OpenBciDevice, MarkerHandler

device = OpenBciDevice(port="/dev/ttyUSB0")
device.connect()
device.start_stream()

# Create a marker handler
markers = MarkerHandler(device)

# Add markers during an experiment
markers.add_marker(1, description="Stimulus onset")
# ... run experiment ...
markers.add_marker(2, description="Response")

# Get data with markers
data = device.get_data()
all_markers = markers.get_markers()

# Clean up
device.stop_stream()
device.disconnect()
```

## Next Steps

For integration with the Model Context Protocol, see the [MCP Module API](mcp-module.md) documentation. 