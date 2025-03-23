"""
Main entry point for the BCI-MCP application.
Provides a command-line interface for controlling the application.
"""

import argparse
import logging
import os
import signal
import sys
import time

from bci.brain_interface import BrainInterface, list_serial_ports
from mcp.server import run_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bci-mcp.log')
    ]
)
logger = logging.getLogger("bci-mcp")

def signal_handler(sig, frame):
    """Handle interrupt signals gracefully"""
    logger.info("Shutting down BCI-MCP application...")
    sys.exit(0)

def run_standalone_mode(args):
    """Run in standalone BCI mode without MCP server"""
    logger.info("Starting BCI in standalone mode...")
    
    # Initialize brain interface
    device = BrainInterface(port=args.port)
    
    if args.list_ports:
        list_serial_ports()
        return
    
    # Connect to device
    if device.connect():
        logger.info(f"Connected to device on {device.port}")
        
        # Calibrate if requested
        if args.calibrate:
            logger.info(f"Calibrating device for {args.calibrate_duration} seconds...")
            device.calibrate(duration=args.calibrate_duration)
        
        # Record session if requested
        if args.record:
            logger.info(f"Recording session for {args.record} seconds...")
            device.run_session(duration=args.record, plot=args.plot, save=True, format=args.format)
        
        # Disconnect
        device.disconnect()
    else:
        logger.error(f"Failed to connect to device on {device.port}")

def run_interactive_mode():
    """Run in interactive console mode"""
    logger.info("Starting BCI in interactive mode...")
    
    # Initialize brain interface
    device = BrainInterface()
    
    # Clear screen function
    clear_screen = lambda: os.system('cls' if os.name == 'nt' else 'clear')
    
    running = True
    while running:
        clear_screen()
        print("\n===== BCI-MCP Interactive Console =====")
        print(f"Serial Port: {device.port or 'Not set'}")
        print(f"Status: {'Running' if device.streaming else 'Stopped'}")
        
        if device.streaming and device.start_time:
            elapsed = time.time() - device.start_time
            minutes, seconds = divmod(int(elapsed), 60)
            print(f"Running Time: {minutes}m {seconds}s")
            print(f"Detected Events: {device.event_count}")
            if elapsed > 0:
                print(f"Event Rate: {(device.event_count / (elapsed/60)):.2f} events/minute")
        
        print("\nOptions:")
        print("1. Select Serial Port")
        print("2. Start Stream")
        print("3. Stop Stream")
        print("4. Calibrate")
        print("5. Run Session (60s)")
        print("6. Plot Data")
        print("7. Save Data")
        print("8. Adjust Settings")
        print("0. Exit")
        
        choice = input("\nSelect option: ")
        
        if choice == '1':
            ports = list_serial_ports()
            if ports:
                try:
                    port_num = int(input("Select port number: "))
                    if 1 <= port_num <= len(ports):
                        if device.streaming:
                            device.stop_stream()
                        device.disconnect()
                        device.port = ports[port_num-1]
                        print(f"Port set to {ports[port_num-1]}")
                    else:
                        print("Invalid port number")
                except ValueError:
                    print("Please enter a number")
            input("Press Enter to continue...")
        
        elif choice == '2':
            if not device.streaming:
                device.start_stream()
            else:
                print("Stream already running")
            input("Press Enter to continue...")
        
        elif choice == '3':
            if device.streaming:
                device.stop_stream()
            else:
                print("Stream already stopped")
            input("Press Enter to continue...")
        
        elif choice == '4':
            duration = 10
            try:
                user_duration = input("Enter calibration duration in seconds (default 10): ")
                if user_duration.strip():
                    duration = int(user_duration)
            except ValueError:
                print("Invalid duration. Using default 10 seconds")
            
            device.calibrate(duration)
            input("Press Enter to continue...")
        
        elif choice == '5':
            session_duration = 60
            try:
                user_duration = input("Enter session duration in seconds (default 60): ")
                if user_duration.strip():
                    session_duration = int(user_duration)
            except ValueError:
                print("Invalid duration. Using default 60 seconds")
            
            device.run_session(session_duration, plot=True, save=True)
            input("Press Enter to continue...")
        
        elif choice == '6':
            device.plot_data(save=True)
            input("Press Enter to continue...")
        
        elif choice == '7':
            format_choice = input("Select format (npz, csv, pkl) [default=npz]: ").lower() or 'npz'
            if format_choice in ['npz', 'csv', 'pkl']:
                device.save_data(format=format_choice)
            else:
                print(f"Unsupported format: {format_choice}")
            input("Press Enter to continue...")
        
        elif choice == '8':
            print(f"Current detection threshold (z-score): {device.detection_threshold:.2f}")
            print(f"Current cooldown period: {device.cooldown_period:.2f}s")
            
            try:
                new_threshold = input("Enter new detection threshold (or press Enter to keep current): ")
                if new_threshold.strip():
                    device.detection_threshold = float(new_threshold)
                
                new_cooldown = input("Enter new cooldown period in seconds (or press Enter to keep current): ")
                if new_cooldown.strip():
                    device.cooldown_period = float(new_cooldown)
                
                print(f"Settings updated: Threshold={device.detection_threshold:.2f}, Cooldown={device.cooldown_period:.2f}s")
            except ValueError:
                print("Invalid input. Please enter numeric values.")
            
            input("Press Enter to continue...")
        
        elif choice == '0':
            if device.streaming:
                device.stop_stream()
            device.disconnect()
            print("Exiting...")
            running = False
        
        else:
            print("Invalid choice")
            input("Press Enter to continue...")

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description='BCI-MCP: Brain-Computer Interface with Model Context Protocol')
    parser.add_argument('--server', action='store_true', help='Run as MCP server')
    parser.add_argument('--port', type=str, help='Serial port for the BCI device')
    parser.add_argument('--calibrate', action='store_true', help='Run calibration')
    parser.add_argument('--calibrate-duration', type=int, default=10, help='Calibration duration in seconds')
    parser.add_argument('--record', type=int, default=0, help='Record session for specified seconds')
    parser.add_argument('--format', type=str, default='npz', choices=['npz', 'csv', 'pkl'],
                        help='Output file format')
    parser.add_argument('--plot', action='store_true', help='Plot data after recording')
    parser.add_argument('--list-ports', action='store_true', help='List available serial ports')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive console mode')
    
    args = parser.parse_args()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create recordings directory if it doesn't exist
    os.makedirs("recordings", exist_ok=True)
    
    # Determine run mode
    if args.server:
        # Run as MCP server
        logger.info("Starting BCI-MCP server...")
        run_server()
    elif args.interactive:
        # Run in interactive mode
        run_interactive_mode()
    elif args.list_ports or args.port or args.calibrate or args.record > 0:
        # Run in standalone mode with command-line arguments
        run_standalone_mode(args)
    else:
        # Default to interactive mode if no specific mode is selected
        run_interactive_mode()

if __name__ == "__main__":
    main()