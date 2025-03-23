# BCI Features

Brain-Computer Interfaces (BCIs) enable direct communication between the brain and external devices. Our implementation provides a comprehensive set of features for neural signal acquisition, processing, and utilization.

## Core BCI Features

### 1. Neural Signal Acquisition

Our BCI system supports real-time acquisition of electrical signals from brain activity through various interfaces:

- **Serial Port Interface**: Connect to various EEG devices via a standard serial port
- **Multi-Channel Support**: Process data from single or multiple EEG channels
- **High Sampling Rate**: Capture neural signals at 250Hz (configurable)
- **Raw Data Access**: Direct access to unprocessed neural data for custom analysis

### 2. Signal Processing Pipeline

The BCI module implements a sophisticated signal processing pipeline:

- **Pre-processing Filters**:
  - Bandpass filtering (1-45Hz) to focus on relevant neural frequencies
  - Notch filtering (50/60Hz) to remove power line interference
  - Artifact rejection to minimize non-neural signals

- **Feature Extraction**:
  - Time-domain analysis for event detection
  - Z-score normalization for threshold-based detection
  - Sliding window analysis for real-time processing

- **Classification**:
  - Threshold-based event detection
  - Customizable detection parameters
  - Cooldown mechanisms to prevent false positives

### 3. Command Generation

The system converts neural signals into commands that can control external devices:

- **Event Detection**: Identify specific neural patterns like blinks or movements
- **Command Mapping**: Associate neural events with specific commands or actions
- **Timing Control**: Precise control over event detection timing and cooldown periods
- **Callback System**: Register custom handlers for detected neural events

### 4. Feedback Mechanisms

Feedback is crucial for BCI learning and adaptation:

- **Real-time Visualization**: Display EEG signals and detected events in real-time
- **Visual Feedback**: Visual indicators when neural events are detected
- **Session Statistics**: Provide metrics on detection rate, accuracy, and timing
- **Calibration Guidance**: Help users understand optimal signal production

### 5. Persistence and Analysis

The system provides comprehensive data storage and analysis tools:

- **Multiple Data Formats**: Save data in NPZ, CSV, or PKL formats
- **Session Recording**: Complete session data collection with timestamps
- **Offline Analysis**: Tools for post-session review and analysis
- **Data Export**: Easy export for use with external analysis tools

## Advanced Features

### Calibration System

The BCI system includes an adaptive calibration system:

- **Personalized Thresholds**: Determine optimal detection thresholds for each user
- **Baseline Recording**: Establish individual baseline neural activity
- **Noise Level Estimation**: Automatically calculate signal-to-noise ratio
- **Parameter Adjustment**: Fine-tune detection parameters based on calibration data

### Interactive Control

Our implementation provides multiple control interfaces:

- **Command-line Interface**: Control BCI operations via simple terminal commands
- **Interactive Console**: User-friendly menu-driven interface for non-technical users
- **Programmatic API**: Python API for custom application development
- **MCP Integration**: Model Context Protocol for AI-enhanced capabilities

### Visualization Tools

The BCI system includes comprehensive visualization capabilities:

- **Real-time Signal Plotting**: View EEG data as it's being recorded
- **Multi-view Display**: Simultaneously view raw and filtered signals
- **Event Marking**: Visual indicators for detected neural events
- **Session Overview**: Summary visualizations of recording sessions

## Extensibility

The system is designed for easy extension and customization:

- **Modular Architecture**: Clearly separated components for easy modification
- **Event Callbacks**: Register custom handlers for neural events
- **Custom Processing**: Add specialized signal processing algorithms
- **Hardware Abstraction**: Support for different EEG hardware through a common interface

## Use Cases

Our BCI implementation supports numerous applications:

- **Assistive Technology**: Enable control of devices for individuals with limited mobility
- **Research**: Neural data collection and analysis for scientific studies
- **Human-Computer Interaction**: Novel input modalities for computer control
- **Biofeedback**: Help users improve awareness and control of neural activity