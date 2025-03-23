# MCP Module API Reference

This document provides a comprehensive reference for the Model Context Protocol (MCP) module API, which facilitates the integration of brain-computer interface data with large language models.

## Core Classes

### `McpClient`

The main client class for interacting with the Model Context Protocol.

```python
class McpClient:
    def __init__(self, api_key=None, api_endpoint=None, model="default"):
        """
        Initialize an MCP client.
        
        Args:
            api_key (str, optional): API key for authentication
            api_endpoint (str, optional): Custom API endpoint URL
            model (str): Model identifier to use
        """
        pass
    
    def query(self, prompt, context=None, options=None):
        """
        Send a query to the MCP API.
        
        Args:
            prompt (str): The main prompt text
            context (dict, optional): Additional context data, including BCI data
            options (dict, optional): Query options like temperature, max_tokens, etc.
            
        Returns:
            McpResponse: Response object containing the model's output
        """
        pass
    
    def streaming_query(self, prompt, context=None, options=None, callback=None):
        """
        Send a streaming query to the MCP API.
        
        Args:
            prompt (str): The main prompt text
            context (dict, optional): Additional context data, including BCI data
            options (dict, optional): Query options like temperature, max_tokens, etc.
            callback (callable, optional): Function to call with each chunk of the response
            
        Returns:
            Generator[str]: Generator yielding response chunks
        """
        pass
    
    def feedback(self, session_id, feedback_data):
        """
        Send feedback about a previous response.
        
        Args:
            session_id (str): Session ID from a previous query
            feedback_data (dict): Feedback information
            
        Returns:
            bool: True if feedback was successfully submitted
        """
        pass
```

### `McpResponse`

Class representing a response from the MCP API.

```python
class McpResponse:
    def __init__(self, response_data):
        """
        Initialize an MCP response.
        
        Args:
            response_data (dict): Raw response data from the API
        """
        pass
    
    @property
    def text(self):
        """
        Get the text content of the response.
        
        Returns:
            str: Response text
        """
        pass
    
    @property
    def session_id(self):
        """
        Get the session ID for this response.
        
        Returns:
            str: Session ID for tracking and feedback
        """
        pass
    
    @property
    def usage(self):
        """
        Get usage information for this response.
        
        Returns:
            dict: Token usage information
        """
        pass
    
    @property
    def metadata(self):
        """
        Get additional metadata from the response.
        
        Returns:
            dict: Response metadata
        """
        pass
```

### `BciContextProcessor`

Class for processing BCI data into a format suitable for the MCP.

```python
class BciContextProcessor:
    def __init__(self, features=None):
        """
        Initialize a BCI context processor.
        
        Args:
            features (list, optional): List of feature extractors to use
        """
        pass
    
    def process(self, bci_data):
        """
        Process raw BCI data into a context format.
        
        Args:
            bci_data (numpy.ndarray): Raw BCI data
            
        Returns:
            dict: Processed context data
        """
        pass
    
    def add_feature_extractor(self, extractor):
        """
        Add a feature extractor to the processor.
        
        Args:
            extractor (FeatureExtractor): Feature extractor instance
            
        Returns:
            self: For method chaining
        """
        pass
```

## Feature Extractors

```python
class FeatureExtractor:
    """Base class for all feature extractors."""
    
    def extract(self, data):
        """
        Extract features from BCI data.
        
        Args:
            data (numpy.ndarray): BCI data
            
        Returns:
            dict: Extracted features
        """
        pass

class PowerBandExtractor(FeatureExtractor):
    """Extract power in specific frequency bands."""
    
    def __init__(self, bands=None, sampling_rate=250):
        """
        Initialize a power band extractor.
        
        Args:
            bands (dict, optional): Dictionary of frequency bands
            sampling_rate (int): Sampling rate of the data in Hz
        """
        pass

class ConnectivityExtractor(FeatureExtractor):
    """Extract connectivity metrics between channels."""
    
    def __init__(self, method="coherence"):
        """
        Initialize a connectivity extractor.
        
        Args:
            method (str): Connectivity method to use
        """
        pass
```

## Utility Functions

### Authentication

```python
def load_api_key(key_file=None):
    """
    Load an API key from a file or environment variable.
    
    Args:
        key_file (str, optional): Path to a file containing the API key
        
    Returns:
        str: The API key
    """
    pass

def generate_auth_header(api_key):
    """
    Generate an authentication header for API requests.
    
    Args:
        api_key (str): API key
        
    Returns:
        dict: Authentication header
    """
    pass
```

### Context Management

```python
def merge_contexts(contexts):
    """
    Merge multiple context dictionaries.
    
    Args:
        contexts (list): List of context dictionaries
        
    Returns:
        dict: Merged context
    """
    pass

def compress_context(context, max_size=None):
    """
    Compress a context to reduce its size.
    
    Args:
        context (dict): Context to compress
        max_size (int, optional): Maximum size in bytes
        
    Returns:
        dict: Compressed context
    """
    pass
```

## Exception Classes

```python
class McpError(Exception):
    """Base exception class for all MCP-related errors."""
    pass

class ApiConnectionError(McpError):
    """Exception raised when connection to the MCP API fails."""
    pass

class AuthenticationError(McpError):
    """Exception raised when authentication fails."""
    pass

class QueryError(McpError):
    """Exception raised when there's an error processing a query."""
    pass

class ContextProcessingError(McpError):
    """Exception raised when there's an error processing context data."""
    pass
```

## Usage Examples

```python
# Example 1: Basic query with BCI data
from src.mcp import McpClient
from src.bci import OpenBciDevice
from src.mcp.context import BciContextProcessor

# Initialize BCI device and client
device = OpenBciDevice(port="/dev/ttyUSB0")
client = McpClient(api_key="your_api_key")
processor = BciContextProcessor()

# Collect and process BCI data
device.connect()
device.start_stream()
bci_data = device.get_data(samples=500)
context = processor.process(bci_data)

# Send query with BCI context
response = client.query(
    prompt="What can you infer about my cognitive state?",
    context=context
)

print(response.text)

# Example 2: Streaming response with feedback
def handle_chunk(chunk):
    print(chunk, end="", flush=True)

response = client.streaming_query(
    prompt="Generate a meditation based on my current state.",
    context=context,
    callback=handle_chunk
)

# Send feedback about the response
client.feedback(
    session_id=response.session_id,
    feedback_data={"rating": 4, "comments": "Very helpful meditation"}
)
```

## Integrating with the BCI Module

The MCP module is designed to work closely with the BCI module. Typically, you would:

1. Collect data from a BCI device
2. Process the data using signal processing tools
3. Convert the processed data into a context format
4. Send the context along with a prompt to the MCP API
5. Process and use the response

For more information on collecting BCI data, see the [BCI Module API](bci-module.md) documentation. 