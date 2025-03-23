# Installation

This guide will help you set up the BCI-MCP system on your machine.

## Prerequisites

Before installing the BCI-MCP system, ensure you have the following prerequisites:

- Python 3.8 or higher
- Git
- Docker and Docker Compose (for containerized deployment)
- 4GB RAM minimum (8GB recommended)

## Installation Methods

You can install BCI-MCP using one of the following methods:

### Method 1: Direct Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/enkhbold470/bci-mcp.git
   cd bci-mcp
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Method 2: Docker Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/enkhbold470/bci-mcp.git
   cd bci-mcp
   ```

2. Build and run the Docker containers:
   ```bash
   docker-compose up -d
   ```

## Verifying Installation

To verify that the installation was successful:

1. Run the built-in test script:
   ```bash
   python src/test_installation.py
   ```

2. Check for the success message indicating that all components are installed correctly.

## Next Steps

After successfully installing BCI-MCP, proceed to the [Quick Start](quick-start.md) guide to begin using the system. 