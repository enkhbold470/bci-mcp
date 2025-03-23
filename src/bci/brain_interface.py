"""
Core Brain-Computer Interface module for signal acquisition and processing.
Includes real-time signal processing, feature extraction, and command generation.
"""

import numpy as np
import serial
import time
from threading import Thread
import os
import matplotlib.pyplot as plt
from datetime import datetime
import pickle
import csv
from scipy import signal

# Constants
SAMPLE_RATE = 250  # Typically 250Hz for consumer EEG
NOTCH_FREQ = 60.0  # Power line frequency to filter out
BUFFER_SIZE = 250 * 5  # 5 seconds of data
EEG_CHANNELS = 1  # Number of channels
DEFAULT_PORT = '/dev/tty.usbmodem1101'  # Default serial port

class BrainInterface:
    """Core BCI module for real-time neural signal processing"""
    
    def __init__(self, port=None, channels=EEG_CHANNELS):
        # Serial port settings
        self.port = port or DEFAULT_PORT
        self.baudrate = 115200
        self.serial = None
        
        # Data buffers
        self.channels = channels
        self.raw_buffer = np.zeros((self.channels, BUFFER_SIZE))
        self.filtered_buffer = np.zeros((self.channels, BUFFER_SIZE))
        self.timestamps = np.zeros(BUFFER_SIZE)
        self.event_timestamps = []
        
        # Processing state
        self.running = False
        self.streaming = False
        self.filter_state = None
        self.current_sample_idx = 0
        self.start_time = None
        self.event_count = 0
        self.last_event_time = 0
        
        # Detection parameters
        self.cooldown_period = 0.5  # Minimum time between events (seconds)
        self.detection_threshold = 50.0  # Z-score threshold
        self.window_size = 50  # Window size for detection (200ms at 250Hz)
        
        # Create output directories
        self.data_dir = "recordings"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Device type
        self.device_type = "BCI_MCP_Device"
        
        # Prepare filters
        self._setup_filters()
    
    def _setup_filters(self):
        """Configure signal processing filters"""
        # 1-45Hz bandpass filter (standard for EEG)
        self.bp_filter_b, self.bp_filter_a = signal.butter(4, [1.0/125, 45.0/125], btype='bandpass')
        
        # 60Hz notch filter (or 50Hz for EU)
        nyq = 0.5 * SAMPLE_RATE
        notch_freq = NOTCH_FREQ / nyq
        notch_width = 0.1  # Width of the notch
        self.notch_b, self.notch_a = signal.iirnotch(notch_freq, 30.0)
    
    def _apply_filters(self, data):
        """Apply filters to the EEG data"""
        # Use filtfilt for zero-phase filtering (better for offline analysis)
        if len(data) > 10:  # Need enough samples for filtfilt
            # Apply bandpass (1-45Hz)
            filtered = signal.filtfilt(self.bp_filter_b, self.bp_filter_a, data)
            # Apply notch (remove power line noise)
            filtered = signal.filtfilt(self.notch_b, self.notch_a, filtered)
        else:
            filtered = data
        return filtered
    
    def connect(self):
        """Connect to the EEG device"""
        if not self.port:
            print("No port specified. Please select a port.")
            return False
        
        try:
            self.serial = serial.Serial(self.port, self.baudrate)
            print(f"Connected to {self.port} at {self.baudrate} baud")
            time.sleep(2)  # Wait for device to initialize
            self.running = True
            return True
        except Exception as e:
            print(f"Error connecting to serial port: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the EEG device"""
        if self.serial and self.serial.is_open:
            self.stop_stream()
            self.serial.close()
            self.running = False
            print("Disconnected from device")
    
    def start_stream(self):
        """Start streaming data from the device"""
        if not self.running:
            if not self.connect():
                return False
        
        self.streaming = True
        self.start_time = time.time()
        self.current_sample_idx = 0
        self.event_count = 0
        self.event_timestamps = []
        
        # Start reading thread
        self.stream_thread = Thread(target=self._stream_data)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        
        print("Started EEG stream")
        return True
    
    def stop_stream(self):
        """Stop streaming data"""
        self.streaming = False
        print("Stopped EEG stream")
    
    def _stream_data(self):
        """Stream data from the device (runs in thread)"""
        while self.streaming and self.serial and self.serial.is_open:
            if self.serial.in_waiting:
                try:
                    line = self.serial.readline().decode('utf-8').strip()
                    sample = int(line)
                    
                    # Process signed value if needed (24-bit ADC data)
                    if sample > 0x800000:
                        sample = sample - 0x1000000
                    
                    # Store sample in circular buffer
                    buffer_idx = self.current_sample_idx % BUFFER_SIZE
                    self.raw_buffer[0, buffer_idx] = sample
                    self.timestamps[buffer_idx] = time.time()
                    
                    # Apply real-time filter
                    if self.filter_state is None:
                        filtered_sample, self.filter_state = signal.lfilter(
                            self.bp_filter_b, self.bp_filter_a, 
                            [sample], zi=signal.lfilter_zi(self.bp_filter_b, self.bp_filter_a) * sample
                        )
                    else:
                        filtered_sample, self.filter_state = signal.lfilter(
                            self.bp_filter_b, self.bp_filter_a, 
                            [sample], zi=self.filter_state
                        )
                    
                    # Apply notch filter
                    filtered_sample, self.notch_state = signal.lfilter(
                        self.notch_b, self.notch_a,
                        filtered_sample, zi=signal.lfilter_zi(self.notch_b, self.notch_a) * filtered_sample
                    ) if hasattr(self, 'notch_state') else (filtered_sample, 
                                                       signal.lfilter_zi(self.notch_b, self.notch_a) * filtered_sample[0])
                    
                    # Store filtered sample
                    self.filtered_buffer[0, buffer_idx] = filtered_sample[0]
                    
                    # Check for neural events after we have enough data
                    if self.current_sample_idx >= self.window_size:
                        self._detect_neural_event(buffer_idx)
                    
                    self.current_sample_idx += 1
                
                except (ValueError, UnicodeDecodeError) as e:
                    print(f"Error parsing data: {e}")
            
            # Small sleep to prevent CPU hogging
            time.sleep(0.001)
    
    def _detect_neural_event(self, current_idx):
        """Detect neural events using thresholding"""
        # Get window of data from circular buffer
        window_indices = [(current_idx - i) % BUFFER_SIZE 
                          for i in range(self.window_size)]
        window_data = self.filtered_buffer[0, window_indices]
        
        # Calculate z-score of window
        if np.std(window_data) > 0:
            z_scores = (window_data - np.mean(window_data)) / np.std(window_data)
            max_z = np.max(np.abs(z_scores))
            
            # Check for neural event
            current_time = time.time()
            if (max_z > self.detection_threshold and 
                (current_time - self.last_event_time) > self.cooldown_period):
                self.event_count += 1
                self.event_timestamps.append(current_time)
                self.last_event_time = current_time
                
                # Calculate event rate
                elapsed_min = (current_time - self.start_time) / 60
                if elapsed_min > 0:
                    event_rate = self.event_count / elapsed_min
                    print(f"\nNEURAL EVENT DETECTED! Total: {self.event_count}, "
                          f"Rate: {event_rate:.1f} events/min")
                
                # Trigger the callback if one is registered
                if hasattr(self, 'event_callback') and callable(self.event_callback):
                    self.event_callback(self.event_count, current_time - self.start_time)
    
    def register_event_callback(self, callback_function):
        """Register a callback function to be called when a neural event is detected"""
        self.event_callback = callback_function
    
    def calibrate(self, duration=10):
        """Calibrate detection parameters based on baseline reading"""
        print(f"Calibrating for {duration} seconds. Please relax...")
        
        # Start streaming if not already
        was_streaming = self.streaming
        if not self.streaming:
            self.start_stream()
        
        # Collect baseline data
        start_time = time.time()
        cal_start_idx = self.current_sample_idx
        
        # Wait for calibration duration
        while (time.time() - start_time) < duration:
            print(f"\rCalibrating: {int(time.time() - start_time)}/{duration} seconds",
                  end="", flush=True)
            time.sleep(0.5)
        
        # Extract calibration data
        cal_end_idx = self.current_sample_idx
        cal_samples = cal_end_idx - cal_start_idx
        
        # If we have a full buffer, get the most recent data
        if cal_samples > BUFFER_SIZE:
            calibration_data = self.filtered_buffer[0, :]
        else:
            # Get only the data collected during calibration
            indices = [i % BUFFER_SIZE for i in range(cal_start_idx, cal_end_idx)]
            calibration_data = self.filtered_buffer[0, indices]
        
        # Calculate statistics for setting thresholds
        if len(calibration_data) > SAMPLE_RATE:  # Ensure we have at least 1s of data
            # Get baseline signal statistics
            baseline_std = np.std(calibration_data)
            baseline_mean = np.mean(calibration_data)
            
            # Calculate typical noise level
            noise_level = baseline_std * 2
            
            # Set detection threshold as multiple of noise
            # Typical neural events produce 4-8 times the baseline variation
            self.detection_threshold = 5.0  # Z-score threshold
            
            print(f"\nCalibration complete!")
            print(f"Baseline mean: {baseline_mean:.2f}")
            print(f"Baseline standard deviation: {baseline_std:.2f}")
            print(f"Detection threshold (z-score): {self.detection_threshold:.2f}")
            
        else:
            print("\nNot enough data for calibration.")
        
        # Return to previous streaming state if we weren't streaming before
        if not was_streaming:
            self.stop_stream()
    
    def plot_data(self, save=False):
        """Plot collected EEG data and detected events"""
        if self.current_sample_idx == 0:
            print("No data to plot")
            return
        
        # Get the most recent data in chronological order
        if self.current_sample_idx < BUFFER_SIZE:
            # Buffer not filled yet
            plot_indices = range(0, self.current_sample_idx)
            raw_data = self.raw_buffer[0, plot_indices]
            filtered_data = self.filtered_buffer[0, plot_indices]
            time_axis = self.timestamps[plot_indices] - self.start_time
        else:
            # Buffer is full - get data in correct order from circular buffer
            current_pos = self.current_sample_idx % BUFFER_SIZE
            plot_indices = [(current_pos + i) % BUFFER_SIZE for i in range(BUFFER_SIZE)]
            raw_data = self.raw_buffer[0, plot_indices]
            filtered_data = self.filtered_buffer[0, plot_indices]
            time_axis = np.linspace(
                self.timestamps[plot_indices[0]] - self.start_time,
                self.timestamps[plot_indices[-1]] - self.start_time,
                len(plot_indices)
            )
        
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Plot raw signal
        plt.subplot(3, 1, 1)
        plt.plot(time_axis, raw_data)
        plt.title('Raw EEG Signal')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        
        # Plot filtered signal
        plt.subplot(3, 1, 2)
        plt.plot(time_axis, filtered_data)
        plt.title('Filtered EEG Signal (1-45Hz)')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        
        # Plot events
        plt.subplot(3, 1, 3)
        if self.event_timestamps and self.start_time:
            event_times = [(t - self.start_time) for t in self.event_timestamps]
            plt.vlines(event_times, 0, 1, colors='r', linewidth=2)
            plt.scatter(event_times, [0.5] * len(event_times), color='r', s=50)
        plt.title(f'Detected Neural Events (total: {self.event_count})')
        plt.xlabel('Time (s)')
        plt.ylim(-0.1, 1.1)
        plt.yticks([])
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_dir}/eeg_events_{timestamp}.png"
            plt.savefig(filename)
            print(f"Plot saved to {filename}")
        
        plt.show()
    
    def save_data(self, format='npz'):
        """Save collected data to file in specified format"""
        if self.current_sample_idx == 0:
            print("No data to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get data in chronological order
        if self.current_sample_idx < BUFFER_SIZE:
            # Buffer not filled yet
            plot_indices = range(0, self.current_sample_idx)
            raw_data = self.raw_buffer[0, plot_indices]
            filtered_data = self.filtered_buffer[0, plot_indices]
            time_data = self.timestamps[plot_indices] - self.start_time
        else:
            # Buffer is full - get data in correct order from circular buffer
            current_pos = self.current_sample_idx % BUFFER_SIZE
            plot_indices = [(current_pos + i) % BUFFER_SIZE for i in range(BUFFER_SIZE)]
            raw_data = self.raw_buffer[0, plot_indices]
            filtered_data = self.filtered_buffer[0, plot_indices]
            time_data = self.timestamps[plot_indices] - self.start_time
        
        # Save in appropriate format
        if format.lower() == 'npz':
            filename = f"{self.data_dir}/eeg_data_{timestamp}.npz"
            np.savez(filename, 
                    raw_data=raw_data,
                    filtered_data=filtered_data,
                    timestamps=time_data,
                    event_timestamps=np.array(self.event_timestamps) - self.start_time,
                    sample_rate=SAMPLE_RATE,
                    start_time=self.start_time)
        
        elif format.lower() == 'csv':
            filename = f"{self.data_dir}/eeg_data_{timestamp}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'raw_eeg', 'filtered_eeg', 'is_event'])
                
                # Create an event indicator array
                event_indicators = np.zeros(len(time_data))
                if self.start_time and self.event_timestamps:
                    event_times = np.array(self.event_timestamps) - self.start_time
                    for event_time in event_times:
                        # Find closest timestamp
                        idx = np.abs(time_data - event_time).argmin()
                        event_indicators[idx] = 1
                
                # Write data rows
                for i in range(len(time_data)):
                    writer.writerow([time_data[i], raw_data[i], filtered_data[i], event_indicators[i]])
        
        elif format.lower() == 'pkl':
            filename = f"{self.data_dir}/eeg_data_{timestamp}.pkl"
            data_dict = {
                'raw_data': raw_data,
                'filtered_data': filtered_data,
                'timestamps': time_data,
                'event_timestamps': np.array(self.event_timestamps) - self.start_time if self.event_timestamps else np.array([]),
                'sample_rate': SAMPLE_RATE,
                'start_time': self.start_time,
                'device_info': {
                    'name': self.device_type,
                    'channels': self.channels,
                    'sample_rate': SAMPLE_RATE
                }
            }
            with open(filename, 'wb') as f:
                pickle.dump(data_dict, f)
        
        else:
            print(f"Unsupported format: {format}")
            return None
        
        print(f"Data saved to {filename}")
        return filename

    def run_session(self, duration=60, plot=True, save=True, format='npz'):
        """Run a complete recording session"""
        print(f"Starting {duration} second recording session...")
        
        # Start streaming if not already
        was_streaming = self.streaming
        if not self.streaming:
            self.start_stream()
        
        # Progress indicator
        start = time.time()
        while (time.time() - start) < duration:
            elapsed = int(time.time() - start)
            remaining = duration - elapsed
            print(f"\rRecording: {elapsed}s elapsed, {remaining}s remaining, "
                  f"{self.event_count} events detected", end="", flush=True)
            time.sleep(0.5)
        
        print("\nRecording complete!")
        
        # Calculate statistics
        if self.start_time and self.event_count > 0:
            session_duration_min = duration / 60
            event_rate = self.event_count / session_duration_min
            avg_interval = duration / (self.event_count if self.event_count > 0 else 1)
            
            print(f"\nSession Statistics:")
            print(f"Duration: {session_duration_min:.1f} minutes")
            print(f"Total Events: {self.event_count}")
            print(f"Event Rate: {event_rate:.2f} events/minute")
            print(f"Average Interval: {avg_interval:.2f} seconds")
        
        # Stop streaming if we started it
        if not was_streaming:
            self.stop_stream()
        
        # Save and plot
        if save:
            self.save_data(format=format)
        
        if plot:
            self.plot_data(save=save)

def list_serial_ports():
    """List available serial ports"""
    import serial.tools.list_ports
    
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        print("No serial ports available")
        return []
    
    print("Available ports:")
    for i, port in enumerate(ports):
        print(f"{i+1}: {port.device} - {port.description}")
    
    return [port.device for port in ports]