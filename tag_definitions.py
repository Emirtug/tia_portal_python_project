# Tag Definitions
# Define all tags that will be read/written from PLC

TAGS = {
    'temperature': {
        'db': 1,
        'address': 0,
        'type': 'real',
        'description': 'Temperature Value',
    },
    'pressure': {
        'db': 1,
        'address': 4,
        'type': 'real',
        'description': 'Pressure Value',
    },
    'motor_run': {
        'db': 1,
        'address': 8,
        'type': 'bool',
        'description': 'Motor Running Status',
    },
    'pump_enabled': {
        'db': 1,
        'address': 9,
        'type': 'bool',
        'description': 'Pump Enable Status',
    },
    'error_code': {
        'db': 1,
        'address': 10,
        'type': 'int',
        'description': 'Error Code',
    },
    'production_count': {
        'db': 1,
        'address': 12,
        'type': 'dint',
        'description': 'Production Counter',
    },
}

# Data types mapping
DATA_TYPES = {
    'bool': 1,      # Boolean
    'byte': 1,      # Byte
    'int': 2,       # Integer (16-bit)
    'dint': 4,      # Double Integer (32-bit)
    'real': 4,      # Real (32-bit float)
    'string': None, # String (variable)
}
