
import json
import os
from snap7_connection import PLCConnection, SNAP7_AVAILABLE


class PLCController:
    """PLC connection and tag management"""
    
    def __init__(self, config_file='plc_config.json'):
        self.config_file = config_file
        self.config = {}
        self.plc = PLCConnection()
        self.connected = False
        self.load_config()
    
    def load_config(self):
        """Load settings from config file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.config = {}
        
        if 'simulator_ip' not in self.config:
            self.config['simulator_ip'] = '10.76.106.152'
            self.save_config()
        
        if 'rack' not in self.config:
            self.config['rack'] = 0
        
        if 'slot' not in self.config:
            self.config['slot'] = 1
    
    def save_config(self):
        """Save config to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except IOError:
            pass
    
    def get_simulator_ip(self):
        """Get PLCSim Station IP address"""
        return self.config.get('simulator_ip', '10.76.106.152')
    
    def set_simulator_ip(self, ip):
        """Set PLCSim Station IP address"""
        self.config['simulator_ip'] = ip
        self.save_config()
    
    def connect_plcsim(self):
        """Connect to PLCSim Station"""
        if not SNAP7_AVAILABLE:
            return False, "Snap7 not installed"
        
        ip = self.get_simulator_ip()
        rack = self.config.get('rack', 0)
        slot = self.config.get('slot', 1)
        
        if self.plc.connect(ip, rack, slot):
            self.connected = True
            return True, f"Connected to {ip}"
        else:
            self.connected = False
            return False, f"Failed to connect to {ip}"
    
    def disconnect_plcsim(self):
        """Disconnect from PLCSim Station"""
        if self.plc.disconnect():
            self.connected = False
            return True, "Disconnected"
        return False, "Disconnect failed"
    
    def is_connected(self):
        """Check connection status"""
        return self.connected and self.plc.is_connected()
    
    def send_tag(self, address, value, data_type='Byte'):
        """
        Send value to tag
        
        Args:
            address: PLC address (e.g. "Q64.0", "M0.0", "I0.1")
            value: Value to send
            data_type: Data type ('Bool', 'Byte', 'Int', 'DInt')
        
        Returns:
            (success: bool, message: str)
        """
        if not self.is_connected():
            return False, "Not connected to PLC"
        
        try:
            if data_type == 'Bool':
                bool_val = bool(value)
                result = self.plc.write_bool(address, bool_val)
                if result:
                    return True, f"Sent {bool_val} to {address}"
                else:
                    return False, f"Failed to write to {address}"
            
            elif data_type == 'Byte':
                # Byte değer gönder (0-255)
                byte_val = int(value) & 0xFF
                result = self.plc.write_byte(address, byte_val)
                if result:
                    return True, f"Sent {byte_val} to {address}"
                else:
                    return False, f"Failed to write to {address}"
            
            elif data_type in ['Int', 'DInt']:
                # Integer değer gönder (4 byte)
                int_val = int(value)
                result = self.plc.write_int(address, int_val)
                if result:
                    return True, f"Sent {int_val} to {address}"
                else:
                    return False, f"Failed to write to {address}"
            
            else:
                return False, f"Unsupported data type: {data_type}"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def read_tag(self, address, data_type='Byte'):
        """
        Tag'den değer oku
        
        Args:
            address: PLC adresi
            data_type: Veri tipi
        
        Returns:
            (success: bool, value: any, message: str)
        """
        if not self.is_connected():
            return False, None, "Not connected to PLC"
        
        try:
            if data_type == 'Bool':
                value = self.plc.read_bool(address)
                if value is not None:
                    return True, value, f"Read {value} from {address}"
                else:
                    return False, None, f"Failed to read from {address}"
            
            elif data_type == 'Byte':
                value = self.plc.read_byte(address)
                if value is not None:
                    return True, value, f"Read {value} from {address}"
                else:
                    return False, None, f"Failed to read from {address}"
            
            elif data_type in ['Int', 'DInt']:
                value = self.plc.read_int(address)
                if value is not None:
                    return True, value, f"Read {value} from {address}"
                else:
                    return False, None, f"Failed to read from {address}"
            
            else:
                return False, None, f"Unsupported data type: {data_type}"
        
        except Exception as e:
            return False, None, f"Error: {str(e)}"
    
    def send_multiple_tags(self, tags):
        """
        Birden fazla tag'e değer gönder
        
        Args:
            tags: Liste [(address, value, data_type), ...]
        
        Returns:
            (success_count: int, results: list)
        """
        results = []
        success_count = 0
        
        for address, value, data_type in tags:
            success, message = self.send_tag(address, value, data_type)
            results.append((address, success, message))
            if success:
                success_count += 1
        
        return success_count, results


# Test fonksiyonu
def test_plc_controller():
    """Test PLC Controller"""
    controller = PLCController()
    
    print(f"PLCSim IP: {controller.get_simulator_ip()}")
    
    success, message = controller.connect_plcsim()
    print(f"Connection: {message}")
    
    if success:
        success, msg = controller.send_tag("Q64.0", 5, "Byte")
        print(f"Send: {msg}")
        
        success, value, msg = controller.read_tag("Q64.0", "Byte")
        print(f"Read: {msg}")
        
        success, msg = controller.disconnect_plcsim()
        print(f"Disconnect: {msg}")


if __name__ == "__main__":
    test_plc_controller()
