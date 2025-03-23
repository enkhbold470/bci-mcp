# Brain-Computer Interface with Model Context Protocol (BCI-MCP)

This project integrates Brain-Computer Interface (BCI) technology with the Model Context Protocol (MCP) to create a powerful framework for neural signal acquisition, processing, and AI-enabled interactions.

[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://enkhbold470.github.io/bci-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

BCI-MCP combines:

- **Brain-Computer Interface (BCI)**: Real-time acquisition and processing of neural signals
- **Model Context Protocol (MCP)**: Standardized AI communication interface 

This integration enables advanced applications in healthcare, accessibility, research, and human-computer interaction.

## Key Features

### BCI Core Features

- **Neural Signal Acquisition**: Capture electrical signals from brain activity in real-time
- **Signal Processing**: Preprocess, extract features, and classify brain signals
- **Command Generation**: Convert interpreted brain signals into commands
- **Feedback Mechanisms**: Provide feedback to help users improve control
- **Real-time Operation**: Process brain activity with minimal delay

### MCP Integration Features

- **Standardized Context Sharing**: Connect BCI data with AI models using MCP
- **Tool Exposure**: Make BCI functions available to AI applications
- **Composable Workflows**: Build complex operations combining BCI signals and AI processing
- **Secure Data Exchange**: Enable privacy-preserving neural data transmission

## System Architecture

The BCI-MCP system consists of several key components:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  BCI Hardware   │──────│  BCI Software   │──────│   MCP Server    │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └────────┬────────┘
                                                           │
                                                           │
                                                  ┌────────▼────────┐
                                                  │                 │
                                                  │  AI Applications │
                                                  │                 │
                                                  └─────────────────┘
```

## Getting Started

### Prerequisites

- Python 3.10+
- Compatible EEG hardware (or use simulated mode for testing)
- Additional dependencies listed in requirements.txt

### Installation

```bash
# Clone the repository
git clone https://github.com/enkhbold470/bci-mcp.git
cd bci-mcp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Using Docker

For easier setup, you can use Docker:

```bash
# Build and start all services
docker-compose up -d

# Access the documentation at http://localhost:8000
# The MCP server will be available at ws://localhost:8765
```

### Basic Usage

```bash
# Start the MCP server
python src/main.py --server

# Or use the interactive console
python src/main.py --interactive

# List available EEG devices
python src/main.py --list-ports

# Record a 60-second BCI session
python src/main.py --port /dev/tty.usbmodem1101 --record 60
```

## Advanced Applications

The BCI-MCP integration enables a range of cutting-edge applications:

### Healthcare and Accessibility

- **Assistive Technology**: Enable individuals with mobility impairments to control devices
- **Rehabilitation**: Support neurological rehabilitation with real-time feedback
- **Diagnostic Tools**: Aid in diagnosing neurological conditions

### Research and Development

- **Neuroscience Research**: Facilitate studies of brain function and cognition
- **BCI Training**: Accelerate learning and adaptation to BCI control
- **Protocol Development**: Establish standards for neural data exchange

### AI-Enhanced Interfaces

- **Adaptive Interfaces**: Interfaces that adjust based on neural signals and AI assistance
- **Intent Recognition**: Better understanding of user intent through neural signals
- **Augmentative Communication**: Enhanced communication for individuals with speech disabilities

## Documentation

Comprehensive documentation is available on [our GitHub Pages site](https://enkhbold470.github.io/bci-mcp/).

- [Quick Start Guide](https://enkhbold470.github.io/bci-mcp/getting-started/quick-start/)
- [BCI Features](https://enkhbold470.github.io/bci-mcp/features/bci-features/)
- [MCP Integration](https://enkhbold470.github.io/bci-mcp/features/mcp-integration/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the [OpenBCI](https://openbci.com/) project
- Built on the [Model Context Protocol](https://modelcontextprotocol.io/) framework
- Thanks to the neuroscience and AI research communities

## Contact

Enkhbold Ganbold - [GitHub Profile](https://github.com/enkhbold470)

Project Link: [https://github.com/enkhbold470/bci-mcp](https://github.com/enkhbold470/bci-mcp)