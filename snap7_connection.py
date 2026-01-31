
try:
    import snap7
    from snap7.type import Areas
    from snap7.util import get_bool, set_bool
    SNAP7_AVAILABLE = True
except ImportError:
    SNAP7_AVAILABLE = False


class PLCConnection:
    """Manages Snap7 PLC connections"""
    
    def __init__(self):
        self.plc = None
        self.connected = False
        
    def connect(self, ip_address, rack=0, slot=1):
        """
        Connect to PLC
        Args:
            ip_address: IP of PLC
            rack: Rack number (usually 0)
            slot: Slot number (usually 1)
        Returns:
            True if connected, False otherwise
        """
        if not SNAP7_AVAILABLE:
            return False
            
        try:
            self.plc = snap7.client.Client()
            self.plc.connect(ip_address, rack, slot)
            self.connected = self.plc.get_connected()
            return self.connected
        except Exception as e:
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from PLC"""
        if self.plc and self.connected:
            try:
                self.plc.disconnect()
                self.connected = False
                return True
            except Exception as e:
                return False
        return True
    
    def is_connected(self):
        """Check connection status"""
        return self.connected
    
    def parse_address(self, address):
        """
        Parse PLC address format
        Examples: "M0.0", "DB1.DBD0", "I0.1", "Q0.0"
        Returns: (area, db_number, byte, bit) or None if invalid
        """
        try:
            address = address.strip().upper()
            
            # Format: M0.0 (Merker)
            if address.startswith('M'):
                parts = address[1:].split('.')
                if len(parts) == 2:
                    byte_addr = int(parts[0])
                    bit_addr = int(parts[1])
                    return (Areas.MK, 0, byte_addr, bit_addr)
            
            # Format: I0.1 (Input)
            elif address.startswith('I'):
                parts = address[1:].split('.')
                if len(parts) == 2:
                    byte_addr = int(parts[0])
                    bit_addr = int(parts[1])
                    return (Areas.PE, 0, byte_addr, bit_addr)
            
            # Format: Q0.0 (Output)
            elif address.startswith('Q'):
                parts = address[1:].split('.')
                if len(parts) == 2:
                    byte_addr = int(parts[0])
                    bit_addr = int(parts[1])
                    return (Areas.PA, 0, byte_addr, bit_addr)
            
            # Format: DB1.DBD0 (Data Block)
            elif address.startswith('DB'):
                parts = address.split('.')
                if len(parts) == 2:
                    db_num = int(parts[0][2:])
                    offset_str = parts[1]
                    
                    if offset_str.startswith('DBD'):
                        offset = int(offset_str[3:])
                        return (Areas.DB, db_num, offset, None)
                    elif offset_str.startswith('DBB'):
                        offset = int(offset_str[3:])
                        return (Areas.DB, db_num, offset, None)
                    elif offset_str.startswith('DBX'):
                        offset_parts = offset_str[3:].split('.')
                        byte_offset = int(offset_parts[0])
                        bit_offset = int(offset_parts[1])
                        return (Areas.DB, db_num, byte_offset, bit_offset)
            
            return None
        except:
            return None
    
    def read_bool(self, address):
        """Read boolean value from address"""
        if not self.connected:
            return None
        
        parsed = self.parse_address(address)
        if not parsed:
            return None
        
        try:
            area, db_num, byte_addr, bit_addr = parsed
            
            if bit_addr is not None:
                data = self.plc.read_area(area, db_num, byte_addr, 1)
                return get_bool(data, 0, bit_addr)
            else:
                data = self.plc.read_area(area, db_num, byte_addr, 1)
                return data[0] != 0
        except Exception as e:
            return None
    
    def write_bool(self, address, value):
        """Write boolean value to address"""
        if not self.connected:
            return False
        
        parsed = self.parse_address(address)
        if not parsed:
            return False
        
        try:
            area, db_num, byte_addr, bit_addr = parsed
            
            if bit_addr is not None:
                data = self.plc.read_area(area, db_num, byte_addr, 1)
                data_list = list(data)
                set_bool(data_list, 0, bit_addr, value)
                self.plc.write_area(area, db_num, byte_addr, bytes(data_list))
            else:
                byte_val = 1 if value else 0
                self.plc.write_area(area, db_num, byte_addr, bytes([byte_val]))
            
            return True
        except Exception as e:
            return False
    
    def read_byte(self, address):
        """Read byte value from address (1 byte, 0-255)"""
        if not self.connected:
            return None
        
        parsed = self.parse_address(address)
        if not parsed:
            return None
        
        try:
            area, db_num, byte_addr, _ = parsed
            data = self.plc.read_area(area, db_num, byte_addr, 1)
            return int(data[0])
        except Exception as e:
            return None
    
    def write_byte(self, address, value):
        """Write byte value to address (1 byte, 0-255)"""
        if not self.connected:
            return False
        
        parsed = self.parse_address(address)
        if not parsed:
            return False
        
        try:
            area, db_num, byte_addr, _ = parsed
            byte_val = int(value) & 0xFF
            self.plc.write_area(area, db_num, byte_addr, bytes([byte_val]))
            return True
        except Exception as e:
            return False
    
    def read_int(self, address):
        """Read integer value from address (4 bytes)"""
        if not self.connected:
            return None
        
        parsed = self.parse_address(address)
        if not parsed:
            return None
        
        try:
            area, db_num, byte_addr, _ = parsed
            data = self.plc.read_area(area, db_num, byte_addr, 4)
            return int.from_bytes(data[:4], byteorder='big')
        except Exception as e:
            return None
    
    def write_int(self, address, value):
        """Write integer value to address (4 bytes)"""
        if not self.connected:
            return False
        
        parsed = self.parse_address(address)
        if not parsed:
            return False
        
        try:
            area, db_num, byte_addr, _ = parsed
            data = int(value).to_bytes(4, byteorder='big')
            self.plc.write_area(area, db_num, byte_addr, data)
            return True
        except Exception as e:
            return False
