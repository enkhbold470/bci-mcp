# Configuration

This guide explains how to configure the BCI-MCP system for your specific needs.

## Configuration Files

BCI-MCP uses several configuration files:

- `config.yaml`: Main configuration file for the system
- `.env`: Environment variables for Docker and sensitive settings
- `mkdocs.yml`: Documentation site configuration

## Basic Configuration

### config.yaml

The main configuration file supports the following settings:

```yaml
# Basic settings
application:
  name: "BCI-MCP"
  version: "1.0.0"
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# BCI device configuration
bci:
  device_type: "openBCI"  # openBCI, emotiv, neurosky, etc.
  sampling_rate: 250  # Hz
  channels: 8  # Number of EEG channels
  port: "/dev/ttyUSB0"  # Serial port or device path

# MCP settings
mcp:
  api_endpoint: "https://api.example.com/mcp"
  api_key: "${MCP_API_KEY}"  # Loaded from .env file
  model: "default"
  timeout: 30  # seconds
```

### Environment Variables (.env)

Create a `.env` file in the root directory with your sensitive configuration:

```
MCP_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@localhost/bci_mcp
```

## Advanced Configuration

### Signal Processing

Configure signal processing in the `config.yaml` file:

```yaml
signal_processing:
  filters:
    - type: "bandpass"
      low_cutoff: 1  # Hz
      high_cutoff: 50  # Hz
    - type: "notch"
      frequency: 60  # Hz
  
  features:
    - type: "power_spectral_density"
      enabled: true
    - type: "time_domain"
      enabled: true
```

### Model Context Protocol (MCP)

Configure MCP settings for advanced usage:

```yaml
mcp_advanced:
  context_window: 5000  # tokens
  temperature: 0.7
  max_tokens: 2000
  stream_response: true
```

## Configuration Validation

To validate your configuration:

```bash
python src/utils/validate_config.py
```

This will check your configuration files for errors and provide recommendations.

## Next Steps

After configuring your BCI-MCP system, proceed to [BCI Features](../features/bci-features.md) to learn about the available features. 