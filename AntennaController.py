import serial
import time
import threading
import logging
import os
from datetime import datetime
import serial.tools.list_ports

class AntennaController:
    def __init__(self, port, baudrate=115200, timeout=1):
        """
        Initialize the antenna controller
        
        Args:
            port (str): Serial port to connect to
            baudrate (int): Baud rate for the port
            timeout (float): Serial read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.running = False
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(__file__), 'logs_antenna')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f'antenna_data_{timestamp}.txt')
        
        # Create loggers
        self.data_logger = logging.getLogger('antenna_data')
        self.main_logger = logging.getLogger('main')
        
        # Clear any existing handlers
        self.data_logger.handlers.clear()
        self.main_logger.handlers.clear()
        
        # Set logging levels
        self.data_logger.setLevel(logging.INFO)
        self.main_logger.setLevel(logging.INFO)
        
        # Create file handler for data logging (with timestamps)
        file_handler = logging.FileHandler(self.log_file)
        file_formatter = logging.Formatter('%(asctime)s,%(message)s')
        file_handler.setFormatter(file_formatter)
        self.data_logger.addHandler(file_handler)
        
        # Console handler for main logger
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.main_logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate messages
        self.data_logger.propagate = False
        
        self.main_logger.info(f"Antenna Controller initialized:")
        self.main_logger.info(f"Data log: {self.log_file}")
        
    def connect_port(self):
        """Establish connection to the serial port"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.main_logger.info(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            self.main_logger.error(f"Failed to connect to {self.port}: {e}")
            return False
    
    def disconnect_port(self):
        """Close the serial connection"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.main_logger.info("Serial port disconnected")
    
    def send_command(self, command):
        """Send a command over serial"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(command.encode('utf-8'))
                self.main_logger.info(f"Sent command: {command}")
                return True
            except serial.SerialException as e:
                self.main_logger.error(f"Failed to send command: {e}")
                return False
        else:
            self.main_logger.error("Serial port not connected")
            return False
    
    def read_serial_data(self):
        """Read data from the serial port in a separate thread"""
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    if line:
                        # Log with timestamp to file
                        self.data_logger.info(line)
                        # Print to terminal without timestamp
                        print(f"Received: {line}")
                        
            except serial.SerialException as e:
                self.main_logger.error(f"Serial read error: {e}")
                break
            except Exception as e:
                self.main_logger.error(f"Unexpected error: {e}")
                break
                
    def start_controller(self):
        """Start the antenna controller"""
        if not self.connect_port():
            return False
        
        self.running = True
        
        # Start reading thread
        read_thread = threading.Thread(target=self.read_serial_data, daemon=True)
        read_thread.start()
        
        try:
            self.main_logger.info("Antenna Controller started.")
            print(f"Connected to {self.port}")
            print("Press Enter to send 'a' command, or Ctrl+C to stop...")
            
            while self.running:
                try:
                    # Wait for user input (Enter key)
                    input()  # This will block until user presses Enter
                    
                    # Send 'a' command
                    if self.send_command('a'):
                        print("Command 'a' sent!")
                    
                except EOFError:
                    # Handle case where input is closed
                    break
                    
        except KeyboardInterrupt:
            self.main_logger.info("Stopping antenna controller...")
            print("\nStopping antenna controller...")
            self.running = False
            self.disconnect_port()
        
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

def get_port_selection():
    """Get user selection for the serial port"""
    available_ports = list_serial_ports()
    
    if not available_ports:
        print("No serial ports available.")
        return None
    
    try:
        choice = input(f"\nSelect port number (1-{len(available_ports)}): ")
        port_index = int(choice) - 1
        
        if 0 <= port_index < len(available_ports):
            return available_ports[port_index]
        else:
            print("Invalid choice")
            return None
    except ValueError:
        print("Invalid input")
        return None

def get_baud_rate(default=115200):
    """Get baud rate for the port"""
    try:
        baudrate = input(f"Enter baud rate (default {default}): ").strip()
        return int(baudrate) if baudrate else default
    except ValueError:
        print(f"Invalid baud rate, using default {default}")
        return default

def main():
    print("Antenna Controller")
    print("=" * 40)
    
    # Get port selection
    port = get_port_selection()
    if not port:
        return
    
    baudrate = get_baud_rate(115200)
    
    print(f"\nConfiguration:")
    print(f"Port: {port} at {baudrate} baud")
    
    confirm = input("\nProceed with this configuration? (y/n): ").lower()
    if confirm not in ['y', 'yes']:
        print("Cancelled.")
        return
    
    # Create and start the controller
    controller = AntennaController(port, baudrate)
    controller.start_controller()

if __name__ == "__main__":
    main()
