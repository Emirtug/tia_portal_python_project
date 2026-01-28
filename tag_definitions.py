# Tag Definitions
# Tags can be dynamically discovered from PLC
# or defined manually here for specific monitoring

TAGS = {
    'Module02_192.168.0.20': {
        'Temperature': {
            'area': 'DB',
            'db': 1,
            'address': 'DB1.DBD0',  # TIA Format: DB1.DBD0 (DB Double Word at offset 0)
            'type': 'real',
            'description': 'Process Temperature',
        },
        'Pressure': {
            'area': 'DB',
            'db': 1,
            'address': 'DB1.DBD4',  # DB1.DBD4 (offset 4)
            'type': 'real',
            'description': 'System Pressure',
        },
        'Flow_Rate': {
            'area': 'DB',
            'db': 1,
            'address': 'DB1.DBD8',  # DB1.DBD8 (offset 8)
            'type': 'real',
            'description': 'Flow Rate',
        },
        'Motor_Status': {
            'area': 'M',  # Merker (Memory)
            'address': 'M0.0',  # TIA Format: M0.0 (Merker byte 0, bit 0)
            'type': 'bool',
            'description': 'Motor Running Status',
        },
        'Alarm_Code': {
            'area': 'I',  # Input
            'address': 'I0.0',  # TIA Format: I0.0 (Input byte 0, bit 0)
            'type': 'int',
            'description': 'Active Alarm Code',
        },
    },
}

# Data types mapping
DATA_TYPES = {
    'bool': 1,      # Boolean (1 bit)
    'byte': 1,      # Byte (8 bits)
    'int': 2,       # Integer (16-bit)
    'dint': 4,      # Double Integer (32-bit)
    'real': 4,      # Real (32-bit float)
    'string': None, # String (variable)
}

# Memory Areas in Siemens PLC
MEMORY_AREAS = {
    'M': 'Merker (Memory)',       # Internal memory
    'I': 'Input (Inputs/PE)',     # Digital inputs
    'O': 'Output (Outputs/PA)',   # Digital outputs
    'DB': 'Data Block',            # Structured data storage
}

# PLC Areas to read dynamically
PLC_AREAS = {
    'PE': {
        'name': 'Inputs (PE)',
        'area': 'PE',
        'size': 10,  # Read first 10 bytes
    },
    'PA': {
        'name': 'Outputs (PA)',
        'area': 'PA',
        'size': 10,  # Read first 10 bytes
    },
    'MK': {
        'name': 'Markers (MK)',
        'area': 'MK',
        'size': 10,  # Read first 10 bytes
    },
}

