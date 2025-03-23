# MCP Integration

This document explains how the Brain-Computer Interface (BCI) integrates with the Model Context Protocol (MCP) in the BCI-MCP system.

## Overview

The Model Context Protocol (MCP) allows large language models (LLMs) to receive and process brain activity data as additional context. This integration enables AI systems to respond to and adapt based on neural signals, creating a more intuitive human-AI interaction.

## Key Integration Points

### Data Flow from BCI to MCP

```
BCI Device → Signal Processing → Feature Extraction → Context Formatting → MCP API → Language Model
```

1. **BCI Device**: Acquires raw neural signals
2. **Signal Processing**: Filters and cleans the signals
3. **Feature Extraction**: Extracts meaningful features from processed data
4. **Context Formatting**: Converts features into MCP-compatible format
5. **MCP API**: Receives the formatted context
6. **Language Model**: Uses the context for enhanced responses

## Context Data Format

BCI data is structured into the MCP context format as follows:

```json
{
  "bci_data": {
    "metadata": {
      "device_type": "openBCI",
      "channels": 8,
      "sampling_rate": 250,
      "timestamp": 1679569835.245
    },
    "features": {
      "band_powers": {
        "alpha": [0.75, 0.65, 0.82, 0.71, 0.68, 0.72, 0.69, 0.77],
        "beta": [0.45, 0.52, 0.48, 0.51, 0.47, 0.49, 0.50, 0.46],
        "theta": [0.62, 0.58, 0.63, 0.59, 0.61, 0.60, 0.57, 0.64],
        "delta": [0.85, 0.88, 0.83, 0.87, 0.86, 0.84, 0.89, 0.82]
      },
      "connectivity": {
        "coherence": [[0.8, 0.5, 0.3], [0.5, 0.7, 0.4], [0.3, 0.4, 0.9]]
      },
      "statistics": {
        "mean": [0.12, 0.15, 0.11, 0.14, 0.13, 0.12, 0.16, 0.11],
        "variance": [0.05, 0.06, 0.04, 0.05, 0.05, 0.04, 0.06, 0.04]
      },
      "events": [
        {"type": "blink", "timestamp": 1679569835.125, "confidence": 0.92},
        {"type": "attention_spike", "timestamp": 1679569836.352, "confidence": 0.87}
      ]
    },
    "cognitive_state": {
      "attention": 0.75,
      "relaxation": 0.62,
      "cognitive_load": 0.45,
      "arousal": 0.58
    }
  }
}
```

## Feature Extraction

The BCI-MCP system extracts various features from neural signals for use with MCP:

### Spectral Features

- **Band Powers**: Power in different frequency bands (alpha, beta, theta, delta, gamma)
- **Spectral Entropy**: Measure of unpredictability in the frequency domain
- **Peak Frequencies**: Dominant frequencies in the signal

### Temporal Features

- **Event-Related Potentials**: Neural responses to specific events
- **Statistical Measures**: Mean, variance, skewness, kurtosis
- **Signal Complexity**: Measures like Hjorth parameters and sample entropy

### Spatial Features

- **Spatial Filters**: Common Spatial Patterns (CSP) and similar techniques
- **Connectivity Measures**: Coherence, phase synchrony between channels
- **Source Localization**: Estimates of neural source activity

## Cognitive State Estimation

The system estimates cognitive states from BCI data for enhanced interaction:

- **Attention Level**: Focus and engagement
- **Cognitive Load**: Mental workload
- **Emotional State**: Valence and arousal
- **Relaxation**: Calm and meditative states

## Integration Methods

### Direct API Integration

```python
from bci_mcp.devices import OpenBciDevice
from bci_mcp.processing import FeatureExtractor
from bci_mcp.mcp import McpClient

# Initialize BCI device
device = OpenBciDevice(port="/dev/ttyUSB0")
device.connect()
device.start_stream()

# Extract features from BCI data
extractor = FeatureExtractor()
bci_data = device.get_data(seconds=5)
features = extractor.process(bci_data)

# Create MCP client and send query with BCI context
client = McpClient(api_key="your_api_key")
response = client.query(
    prompt="How should I modify my meditation practice based on my current state?",
    context={"bci_data": features}
)

print(response.text)

# Clean up
device.stop_stream()
device.disconnect()
```

### Streaming Integration

For real-time applications, BCI-MCP supports streaming integration:

```python
from bci_mcp.devices import OpenBciDevice
from bci_mcp.processing import StreamProcessor
from bci_mcp.mcp import McpClient

# Initialize components
device = OpenBciDevice(port="/dev/ttyUSB0")
processor = StreamProcessor()
client = McpClient(api_key="your_api_key")

# Configure streaming callback
def on_features_extracted(features):
    response = client.query(
        prompt="Adapt to my current cognitive state",
        context={"bci_data": features}
    )
    print(response.text)

# Start streaming with processing
device.connect()
processor.set_callback(on_features_extracted)
processor.process_stream(device)

# Run for 60 seconds then clean up
import time
time.sleep(60)
processor.stop()
device.disconnect()
```

## Applications

### Adaptive Interfaces

BCI-MCP enables interfaces that adapt to the user's cognitive state:

- Adjusting complexity based on cognitive load
- Providing more assistance when attention decreases
- Adapting information presentation based on emotional state

### Neuro-Augmented AI

Combining neural data with AI capabilities:

- Enhanced creative processes using neural feedback
- Personalized learning systems that adapt to cognitive state
- Meditation and mindfulness applications with neural guidance

### Assistive Technology

BCI-MCP provides powerful assistive capabilities:

- Communication systems for individuals with motor disabilities
- Cognitive assistance that adapts to the user's needs
- Emotional support systems with neural monitoring

## Best Practices

### Privacy and Security

When integrating BCI with MCP, consider these privacy practices:

- Implement data minimization by only sending necessary features
- Use secure, encrypted connections for all data transmission
- Provide clear user control over when and what data is sent
- Consider local processing when possible

### Performance Optimization

For optimal performance:

- Balance feature richness with transmission efficiency
- Implement caching for frequently used context
- Use incremental updates for streaming applications
- Monitor latency and adjust processing accordingly

## Next Steps

For more detailed information on signal processing techniques, see the [Advanced Signal Processing](signal-processing.md) documentation.