import serial
import time
import threading
import logging
import os
from datetime import datetime
import serial.tools.list_ports

class DualSerialLogger:
    def __init__(self, port1, port2, baudrate1=9600, baudrate2=9600, timeout=1):
        """
        Initialize the dual serial logger
        
        Args:
            port1 (str): First serial port
            port2 (str): Second serial port  
            baudrate1 (int): Baud rate for first port
            baudrate2 (int): Baud rate for second port
            timeout (float): Serial read timeout in seconds
        """
        self.port1 = port1
        self.port2 = port2
        self.baudrate1 = baudrate1
        self.baudrate2 = baudrate2
        self.timeout = timeout
        self.serial1 = None
        self.serial2 = None
        self.running = False
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration for both ports"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(__file__), 'dual_logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log filenames with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file1 = os.path.join(log_dir, f'port1_data_{timestamp}.txt')
        self.log_file2 = os.path.join(log_dir, f'port2_data_{timestamp}.txt')
        
        # Create separate loggers for each port
        self.logger1 = logging.getLogger('port1')
        self.logger2 = logging.getLogger('port2')
        self.main_logger = logging.getLogger('main')
        
        # Clear any existing handlers
        self.logger1.handlers.clear()
        self.logger2.handlers.clear()
        self.main_logger.handlers.clear()
        
        # Set logging levels
        self.logger1.setLevel(logging.INFO)
        self.logger2.setLevel(logging.INFO)
        self.main_logger.setLevel(logging.INFO)
        
        # Create file handlers for each port
        file_handler1 = logging.FileHandler(self.log_file1)
        file_handler2 = logging.FileHandler(self.log_file2)
        
        # Create formatters (timestamp,value format)
        formatter = logging.Formatter('%(asctime)s,%(message)s')
        file_handler1.setFormatter(formatter)
        file_handler2.setFormatter(formatter)
        
        # Add file handlers to loggers
        self.logger1.addHandler(file_handler1)
        self.logger2.addHandler(file_handler2)
        
        # Console handler for main logger
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.main_logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate messages
        self.logger1.propagate = False
        self.logger2.propagate = False
        
        self.main_logger.info(f"Logging initialized:")
        self.main_logger.info(f"Port 1 log: {self.log_file1}")
        self.main_logger.info(f"Port 2 log: {self.log_file2}")
        
    def connect_ports(self):
        """Establish connections to both serial ports"""
        try:
            self.serial1 = serial.Serial(
                port=self.port1,
                baudrate=self.baudrate1,
                timeout=self.timeout
            )
            self.main_logger.info(f"Connected to Port 1: {self.port1} at {self.baudrate1} baud")
        except serial.SerialException as e:
            self.main_logger.error(f"Failed to connect to Port 1 ({self.port1}): {e}")
            return False
            
        try:
            self.serial2 = serial.Serial(
                port=self.port2,
                baudrate=self.baudrate2,
                timeout=self.timeout
            )
            self.main_logger.info(f"Connected to Port 2: {self.port2} at {self.baudrate2} baud")
        except serial.SerialException as e:
            self.main_logger.error(f"Failed to connect to Port 2 ({self.port2}): {e}")
            if self.serial1:
                self.serial1.close()
            return False
            
        return True
    
    def disconnect_ports(self):
        """Close both serial connections"""
        if self.serial1 and self.serial1.is_open:
            self.serial1.close()
            self.main_logger.info("Port 1 disconnected")
            
        if self.serial2 and self.serial2.is_open:
            self.serial2.close()
            self.main_logger.info("Port 2 disconnected")
    
    def read_port1(self):
        """Read data from port 1 in a separate thread"""
        sample_count = 0
        while self.running:
            try:
                if self.serial1 and self.serial1.is_open:
                    line = self.serial1.readline().decode('utf-8').strip()
                    if line:
                        sample_count += 1
                        # Log the raw data to file
                        self.logger1.info(line)
                        
                        # Show progress every 100 samples
                        if sample_count % 100 == 0:
                            print(f"Port 1: {sample_count} samples logged")
                            
            except serial.SerialException as e:
                self.main_logger.error(f"Port 1 read error: {e}")
                break
            except Exception as e:
                self.main_logger.error(f"Port 1 unexpected error: {e}")
                break
                
    def read_port2(self):
        """Read data from port 2 in a separate thread"""
        sample_count = 0
        while self.running:
            try:
                if self.serial2 and self.serial2.is_open:
                    line = self.serial2.readline().decode('utf-8').strip()
                    if line:
                        sample_count += 1
                        # Log the raw data to file
                        self.logger2.info(line)
                        
                        # Show progress every 100 samples
                        if sample_count % 100 == 0:
                            print(f"Port 2: {sample_count} samples logged")
                            
            except serial.SerialException as e:
                self.main_logger.error(f"Port 2 read error: {e}")
                break
            except Exception as e:
                self.main_logger.error(f"Port 2 unexpected error: {e}")
                break
    
    def start_logging(self):
        """Start dual logging from both ports"""
        if not self.connect_ports():
            return False
        
        self.running = True
        
        # Start reading threads for both ports
        thread1 = threading.Thread(target=self.read_port1, daemon=True)
        thread2 = threading.Thread(target=self.read_port2, daemon=True)
        
        thread1.start()
        thread2.start()
        
        try:
            self.main_logger.info("Dual serial logging started. Press Ctrl+C to stop...")
            print(f"Logging Port 1 ({self.port1}) to: {self.log_file1}")
            print(f"Logging Port 2 ({self.port2}) to: {self.log_file2}")
            print("Press Ctrl+C to stop...")
            
            while self.running:
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            self.main_logger.info("Stopping dual serial logging...")
            print("\nStopping dual serial logging...")
            self.running = False
            self.disconnect_ports()
        
        return True

def list_serial_ports():
    """List available serial ports"""
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("No serial ports found")
        return []
    
    print("Available serial ports:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")
    
    return [port.device for port in ports]

def get_port_selection(port_name):
    """Get user selection for a specific port"""
    available_ports = list_serial_ports()
    
    if not available_ports:
        print(f"No serial ports available for {port_name}.")
        return None
    
    try:
        choice = input(f"\nSelect {port_name} number (1-{len(available_ports)}): ")
        port_index = int(choice) - 1
        
        if 0 <= port_index < len(available_ports):
            return available_ports[port_index]
        else:
            print("Invalid choice")
            return None
    except ValueError:
        print("Invalid input")
        return None

def get_baud_rate(port_name, default=9600):
    """Get baud rate for a specific port"""
    try:
        baudrate = input(f"Enter baud rate for {port_name} (default {default}): ").strip()
        return int(baudrate) if baudrate else default
    except ValueError:
        print(f"Invalid baud rate, using default {default}")
        return default

def main():
    print("Dual Serial Port Logger")
    print("=" * 40)
    
    # Get first port selection
    print("\n=== Port 1 Selection ===")
    port1 = get_port_selection("Port 1")
    if not port1:
        return
    

    #baudrate1 = get_baud_rate("Port 1", 115200)
    baudrate1 = 115200

    # Get second port selection
    print("\n=== Port 2 Selection ===")
    port2 = get_port_selection("Port 2")
    if not port2:
        return
        
    if port1 == port2:
        print("Error: Both ports cannot be the same!")
        return
    
    #baudrate2 = get_baud_rate("Port 2", 115200)
    baudrate2 = 115200
    
    print(f"\nConfiguration:")
    print(f"Port 1: {port1} at {baudrate1} baud")
    print(f"Port 2: {port2} at {baudrate2} baud")
    
    confirm = input("\nProceed with this configuration? (y/n): ").lower()
    if confirm not in ['y', 'yes']:
        print("Cancelled.")
        return
    
    # Create and start the dual logger
    logger = DualSerialLogger(port1, port2, baudrate1, baudrate2)
    logger.start_logging()

if __name__ == "__main__":
    main()