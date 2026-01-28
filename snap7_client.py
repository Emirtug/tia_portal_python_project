"""
Snap7 PLC Client Module
Handles communication with Siemens PLCs via Snap7
"""

from snap7.client import Client
from snap7 import types as snap7_types
from config import STATIONS, CONNECTION_TIMEOUT
from tag_definitions import TAGS, DATA_TYPES
import struct

class PLCClient:
    def __init__(self):
        self.client = Client()
        self.connected = False
        self.current_station = None
        self.current_config = None
        
    def connect(self, station_name):
        """
        Connect to specified PLC station
        Args:
            station_name: Name of the station from config
        Returns:
            bool: True if connected successfully
        """
        try:
            if self.connected and self.current_station != station_name:
                self.disconnect()
            
            if station_name in STATIONS:
                config = STATIONS[station_name]
                
                # Connect to PLC
                self.client.connect(
                    config['ip'],
                    config['rack'],
                    config['slot'],
                    config['port']
                )
                
                self.connected = True
                self.current_station = station_name
                self.current_config = config
                
                print(f"✓ Connected to {station_name} ({config['ip']})")
                return True
            else:
                print(f"✗ Station {station_name} not found in config")
                return False
                
        except Exception as e:
            print(f"✗ Connection failed: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from current PLC"""
        try:
            if self.client:
                self.client.disconnect()
            self.connected = False
            self.current_station = None
            print("Disconnected from PLC")
        except Exception as e:
            print(f"Error disconnecting: {str(e)}")
    
    def read_tag(self, tag_name):
        """
        Read a single tag value
        Args:
            tag_name: Name of the tag to read
        Returns:
            Value of the tag or None if error
        """
        if not self.connected:
            print("Not connected to any PLC")
            return None
        
        try:
            if tag_name not in TAGS:
                print(f"Tag {tag_name} not defined")
                return None
            
            tag_info = TAGS[tag_name]
            db_number = tag_info['db']
            address = tag_info['address']
            tag_type = tag_info['type']
            
            # Read from DB
            byte_count = DATA_TYPES.get(tag_type, 4)
            data = self.client.db_read(db_number, address, byte_count)
            
            # Parse based on type
            value = self._parse_value(data, tag_type)
            return value
            
        except Exception as e:
            print(f"Error reading tag {tag_name}: {str(e)}")
            return None
    
    def write_tag(self, tag_name, value):
        """
        Write a single tag value
        Args:
            tag_name: Name of the tag to write
            value: Value to write
        Returns:
            bool: True if successful
        """
        if not self.connected:
            print("Not connected to any PLC")
            return False
        
        try:
            if tag_name not in TAGS:
                print(f"Tag {tag_name} not defined")
                return False
            
            tag_info = TAGS[tag_name]
            db_number = tag_info['db']
            address = tag_info['address']
            tag_type = tag_info['type']
            
            # Convert value to bytes
            data = self._encode_value(value, tag_type)
            
            # Write to DB
            self.client.db_write(db_number, address, data)
            print(f"✓ Wrote {tag_name} = {value}")
            return True
            
        except Exception as e:
            print(f"Error writing tag {tag_name}: {str(e)}")
            return False
    
    def read_all_tags(self):
        """
        Read all defined tags at once
        Returns:
            dict: Dictionary with tag names and values
        """
        if not self.connected:
            return {}
        
        results = {}
        for tag_name in TAGS.keys():
            results[tag_name] = self.read_tag(tag_name)
        return results
    
    def read_areas(self):
        """
        Read all PLC areas (Inputs, Outputs, Markers) dynamically
        Returns:
            dict: Nested dictionary with area data and bit values
        """
        if not self.connected:
            return {}
        
        areas_data = {}
        
        try:
            for area_key, area_info in PLC_AREAS.items():
                area_name = area_info['name']
                area = self._get_area_enum(area_info['area'])
                size = area_info['size']
                
                try:
                    data = self.client.read_area(area, 0, 0, size)
                    
                    # Parse bits from bytes
                    bits = {}
                    for byte_idx, byte_val in enumerate(data):
                        for bit_idx in range(8):
                            bit_name = f"{area_info['area']}{byte_idx}.{bit_idx}"
                            bits[bit_name] = bool(byte_val & (1 << bit_idx))
                    
                    areas_data[area_name] = {
                        'raw_bytes': list(data),
                        'bits': bits,
                    }
                    print(f"✓ Read {area_name}")
                except Exception as e:
                    print(f"✗ Error reading {area_name}: {str(e)}")
                    areas_data[area_name] = {'error': str(e)}
            
            return areas_data
            
        except Exception as e:
            print(f"Error reading areas: {str(e)}")
            return {}
    
    @staticmethod
    def _get_area_enum(area_name):
        """Convert area string to snap7 enum"""
        areas = {
            'PE': snap7_types.Areas.PE,     # Inputs
            'PA': snap7_types.Areas.PA,     # Outputs
            'MK': snap7_types.Areas.MK,     # Markers
            'DB': snap7_types.Areas.DB,     # Data blocks
        }
        return areas.get(area_name, snap7_types.Areas.PE)
    
    def get_status(self):
        """Get connection status"""
        return {
            'connected': self.connected,
            'station': self.current_station,
            'ip': self.current_config['ip'] if self.current_config else None,
        }
    
    @staticmethod
    def _parse_value(data, value_type):
        """Parse byte data to Python value"""
        try:
            if value_type == 'bool':
                return bool(data[0] & 0x01)
            elif value_type == 'byte':
                return data[0]
            elif value_type == 'int':
                return struct.unpack('>h', data[:2])[0]  # Big-endian signed short
            elif value_type == 'dint':
                return struct.unpack('>i', data[:4])[0]  # Big-endian signed int
            elif value_type == 'real':
                return struct.unpack('>f', data[:4])[0]  # Big-endian float
            else:
                return None
        except:
            return None
    
    @staticmethod
    def _encode_value(value, value_type):
        """Encode Python value to bytes"""
        try:
            if value_type == 'bool':
                return bytes([1 if value else 0])
            elif value_type == 'byte':
                return bytes([int(value)])
            elif value_type == 'int':
                return struct.pack('>h', int(value))
            elif value_type == 'dint':
                return struct.pack('>i', int(value))
            elif value_type == 'real':
                return struct.pack('>f', float(value))
            else:
                return b'\x00'
        except:
            return b'\x00'
