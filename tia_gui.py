import sys
import json
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QCheckBox, QProgressBar, QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QComboBox, QStyledItemDelegate, QTextEdit)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont

# PLC Controller import (snap7 wrapper)
from plc_controller import PLCController

# Data Types
TIA_DATA_TYPES = ['Bool', 'Byte', 'Char', 'Int', 'UInt', 'DInt', 'UDInt', 'Word', 
                  'DWord', 'Real', 'LReal', 'SInt', 'USInt', 'Date', 'Time', 
                  'Time Of Day', 'S5Time', 'Timer', 'Counter', 'WChar']

# Display Formats
DISPLAY_FORMATS = ['DEC/J', 'DEC', 'Hex', 'BCD', 'Octal', 'Bin', 'Character', 
                   'Unicode character', 'DEC_sequence', 'TIME_OF_DAY', 'Time']

class ComboBoxDelegate(QStyledItemDelegate):
    """Delegate for Type column dropdown in table"""
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(TIA_DATA_TYPES)
        return combo
    
    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        if value in TIA_DATA_TYPES:
            editor.setCurrentText(value)
    
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

class DisplayFormatDelegate(QStyledItemDelegate):
    """Delegate for Display Format column dropdown in table"""
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(DISPLAY_FORMATS)
        return combo
    
    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        if value in DISPLAY_FORMATS:
            editor.setCurrentText(value)
    
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

class TIAPortalGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tag_values_file = 'tag_values.json'
        self.config_file = 'plc_config.json'
        self.tag_values = {}
        self.plc_config = {}
        self.left_panel_visible = True
        self.has_unsaved_changes = False
        
        self.plc_controller = PLCController()
        self.plc_switch_enabled = False
        
        self.snap7_stations = ['PLCSim Station', 'Module02_192.168.0.20']
        
        self.plc_read_timer = QTimer()
        self.plc_read_timer.timeout.connect(self.read_plc_tags)
        self.plc_read_timer.setInterval(1000)
        
        self.load_config()
        self.load_tag_values()
        self.initUI()
        self.apply_theme()
    
    def apply_theme(self):
        """Modern Industrial Theme with Green Accent"""
        stylesheet = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QFrame {
            background-color: #ffffff;
            border-radius: 4px;
        }
        QLabel {
            color: #1a1a1a;
        }
        QComboBox {
            background-color: #ffffff;
            color: #1a1a1a;
            border: 2px solid #e0e0e0;
            border-radius: 4px;
            padding: 5px;
            font-size: 11px;
        }
        QComboBox:hover {
            border: 2px solid #27ae60;
        }
        QComboBox:focus {
            border: 2px solid #27ae60;
            background-color: #f0fdf4;
        }
        QComboBox::drop-down {
            border: none;
            width: 25px;
        }
        QComboBox::down-arrow {
            image: none;
            border: 2px solid #27ae60;
            background-color: #27ae60;
            border-radius: 2px;
            width: 16px;
        }
        """
        self.setStyleSheet(stylesheet)
    
    def initUI(self):
        self.setWindowTitle('PLC Control Lab')
        self.setGeometry(100, 100, 1000, 700)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left Panel
        self.left_panel = QFrame()
        self.left_panel.setMaximumWidth(220)
        self.left_panel.setStyleSheet("background-color: #ffffff; border-right: 1px solid #d3d3d3;")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        station_label = QLabel('Station Selection')
        station_label.setFont(QFont('Arial', 10, QFont.Bold))
        station_label.setStyleSheet("color: #2c3e50;")
        left_layout.addWidget(station_label)
        
        self.station_combo = QComboBox()
        self.station_combo.addItems([
            'Select...',
            'Module01_192.168.0.10',
            'Module02_192.168.0.20',
            'Module03_192.168.0.30',
            'Module04_192.168.0.40',
            'Module05_192.168.0.50',
            'Module06_192.168.0.60',
            'Module07_192.168.0.70',
            'Module08_192.168.0.80',
            'Module09_192.168.0.90',
            'PLCSim Station'
        ])
        self.station_combo.currentIndexChanged.connect(self.on_station_changed)
        left_layout.addWidget(self.station_combo)
        
        # PLCSim IP Settings Button (only visible when PLCSim selected)
        self.simulator_ip_btn = QPushButton('Edit IP')
        self.simulator_ip_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.simulator_ip_btn.clicked.connect(self.edit_simulator_ip)
        self.simulator_ip_btn.setVisible(False)
        left_layout.addWidget(self.simulator_ip_btn)
        
        left_layout.addSpacing(20)
        
        # PLC Status Section
        plc_status_label = QLabel('PLC Status')
        plc_status_label.setFont(QFont('Arial', 10, QFont.Bold))
        plc_status_label.setStyleSheet("color: #2c3e50;")
        left_layout.addWidget(plc_status_label)
        
        plc_status_frame = QFrame()
        plc_status_frame.setStyleSheet("background-color: #f8f8f8; border: 1px solid #e0e0e0; border-radius: 5px; padding: 10px;")
        plc_status_layout = QVBoxLayout(plc_status_frame)
        
        self.plc_status_label = QLabel('● Disconnected')
        self.plc_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        plc_status_layout.addWidget(self.plc_status_label)
        
        self.ip_label = QLabel('IP: -')
        self.ip_label.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        plc_status_layout.addWidget(self.ip_label)
        
        left_layout.addWidget(plc_status_frame)
        
        left_layout.addSpacing(15)
        
        # CAN Bus Status Section
        can_status_label = QLabel('CAN Bus Status')
        can_status_label.setFont(QFont('Arial', 10, QFont.Bold))
        can_status_label.setStyleSheet("color: #2c3e50;")
        left_layout.addWidget(can_status_label)
        
        can_status_frame = QFrame()
        can_status_frame.setStyleSheet("background-color: #f8f8f8; border: 1px solid #e0e0e0; border-radius: 5px; padding: 10px;")
        can_status_layout = QVBoxLayout(can_status_frame)
        
        self.can_status_label = QLabel('● Inactive')
        self.can_status_label.setStyleSheet("color: #95a5a6; font-weight: bold;")
        can_status_layout.addWidget(self.can_status_label)
        
        can_status_layout.addSpacing(10)
        
        plc_switch_container = QHBoxLayout()
        plc_switch_label = QLabel('PLC Connection:')
        plc_switch_label.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 9pt;")
        plc_switch_container.addWidget(plc_switch_label)
        
        self.plc_connection_switch = QCheckBox()
        self.plc_connection_switch.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 40px;
                height: 20px;
                border-radius: 10px;
                background-color: #bdc3c7;
            }
            QCheckBox::indicator:checked {
                background-color: #27ae60;
            }
            QCheckBox::indicator:disabled {
                background-color: #e74c3c;
            }
        """)
        self.plc_connection_switch.setEnabled(False)
        self.plc_connection_switch.stateChanged.connect(self.on_plc_switch_changed)
        plc_switch_container.addWidget(self.plc_connection_switch)
        plc_switch_container.addStretch()
        
        can_status_layout.addLayout(plc_switch_container)
        
        self.plc_connection_status_label = QLabel('Check connection first')
        self.plc_connection_status_label.setStyleSheet("color: #7f8c8d; font-size: 8pt; font-style: italic;")
        can_status_layout.addWidget(self.plc_connection_status_label)
        
        check_connection_btn = QPushButton('Check PLC Connection')
        check_connection_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f6391;
            }
        """)
        check_connection_btn.clicked.connect(self.check_plc_connection)
        can_status_layout.addWidget(check_connection_btn)
        
        left_layout.addWidget(can_status_frame)
        left_layout.addStretch()
        
        footer_label = QLabel('© 2026 Control Lab - Developed by: Emirtug Kacar')
        footer_label.setStyleSheet("color: #95a5a6; font-size: 8pt;")
        footer_label.setWordWrap(True)
        footer_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(footer_label)
        
        main_layout.addWidget(self.left_panel)
        
        # Right Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #ecf0f1; border-radius: 8px; padding: 15px;")
        top_bar_layout = QHBoxLayout(top_bar)
        
        title_label = QLabel('PLC Control Lab')
        title_label.setFont(QFont('Arial', 16, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        top_bar_layout.addWidget(title_label)
        
        top_bar_layout.addStretch()
        
        close_btn = QPushButton('✕')
        close_btn.setFixedSize(40, 40)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 2px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        close_btn.clicked.connect(self.close)
        top_bar_layout.addWidget(close_btn)
        
        right_layout.addWidget(top_bar)
        
        station_row = QHBoxLayout()
        # Station Selection removed from here - kept only on left panel
        
        # Sidebar toggle button
        self.sidebar_toggle_btn = QPushButton('☰')
        self.sidebar_toggle_btn.setFixedSize(35, 35)
        self.sidebar_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar)
        station_row.addWidget(self.sidebar_toggle_btn)
        
        # CAN Bus indicator (label instead of checkbox)
        can_label = QLabel('🔌 CAN Bus')
        can_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 5px;")
        station_row.addWidget(can_label)
        
        station_row.addStretch()
        
        self.connect_btn = QPushButton('CAN Bus: OFF')
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7a7d;
            }
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        station_row.addWidget(self.connect_btn)
        
        right_layout.addLayout(station_row)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #27ae60;
                border-radius: 5px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
            }
        """)
        right_layout.addWidget(self.progress_bar)
        
        table_label = QLabel('Tag Management')
        table_label.setFont(QFont('Arial', 12, QFont.Bold))
        table_label.setStyleSheet("color: #2c3e50; margin-top: 10px;")
        right_layout.addWidget(table_label)
        
        table_toolbar = QHBoxLayout()
        
        add_tag_btn = QPushButton('+ Add New Tag')
        add_tag_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        add_tag_btn.clicked.connect(self.add_new_tag_row)
        table_toolbar.addWidget(add_tag_btn)
        
        save_tags_btn = QPushButton('💾 Save Changes')
        save_tags_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        save_tags_btn.clicked.connect(self.save_tag_changes)
        table_toolbar.addWidget(save_tags_btn)
        
        info_btn = QPushButton('ℹ️')
        info_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                width: 40px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        info_btn.setFixedWidth(45)
        info_btn.clicked.connect(self.show_save_info)
        table_toolbar.addWidget(info_btn)
        
        table_toolbar.addStretch()
        right_layout.addLayout(table_toolbar)
        
        self.tag_table = QTableWidget()
        self.tag_table.setColumnCount(10)
        self.tag_table.setHorizontalHeaderLabels([
            'Tag Name', 'Address', 'Type', 'Value', 
            'Display Format', 'Sending Format', 'PLC Value', 'Status', 'Force', 'Delete'
        ])
        
        self.tag_table.setColumnWidth(0, 120)
        self.tag_table.setColumnWidth(1, 100)
        self.tag_table.setColumnWidth(2, 80)
        self.tag_table.setColumnWidth(3, 80)
        self.tag_table.setColumnWidth(4, 120)
        self.tag_table.setColumnWidth(5, 120)
        self.tag_table.setColumnWidth(6, 100)
        self.tag_table.setColumnWidth(7, 60)
        self.tag_table.setColumnWidth(8, 60)
        self.tag_table.setColumnWidth(9, 60)
        
        self.tag_table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                selection-background-color: #E3F5E6;
                selection-color: #000000;
                gridline-color: #d3d3d3;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 5px;
                border: 1px solid #2c3e50;
                font-weight: bold;
            }
        """)
        
        self.tag_table.setItemDelegateForColumn(2, ComboBoxDelegate(self.tag_table))
        self.tag_table.setItemDelegateForColumn(4, DisplayFormatDelegate(self.tag_table))
        self.tag_table.setItemDelegateForColumn(5, DisplayFormatDelegate(self.tag_table))
        
        self.tag_table.itemChanged.connect(self.on_tag_value_changed)
        
        self.tag_table.setMinimumHeight(200)
        self.tag_table.setMaximumHeight(900)
        
        right_layout.addWidget(self.tag_table)
        
        error_log_label = QLabel('Activity Log')
        error_log_label.setFont(QFont('Arial', 11, QFont.Bold))
        error_log_label.setStyleSheet("color: #2c3e50; margin-top: 10px;")
        right_layout.addWidget(error_log_label)
        
        self.error_log = QTextEdit()
        self.error_log.setReadOnly(True)
        self.error_log.setMaximumHeight(120)
        self.error_log.setStyleSheet("""
            QTextEdit {
                background-color: #f4f4f4;
                color: #c0392b;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }
        """)
        self.error_log.setPlaceholderText("Activity log will appear here...")
        right_layout.addWidget(self.error_log)
        
        main_layout.addWidget(right_panel)
        
        self.current_selected_station = None
        self.current_connecting_station = None
        self.station_connections = {}  # Track connection status per station
        self.station_progress = {}      # Track progress bar value per station
        self.activity_log = ""          # Shared activity log for all stations
        self._old_tag_names = {}
    
    def add_log(self, station, message):
        """Add log message to shared activity log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Format: [HH:MM:SS] [StationName] message
        station_name = station.split('_')[0] if '_' in station else station  # Extract module name
        log_entry = f"[{timestamp}] [{station_name}] {message}"
        
        # Append to shared activity log
        if self.activity_log:
            self.activity_log += f"\n{log_entry}"
        else:
            self.activity_log = log_entry
        
        # Keep only last 100 lines
        lines = self.activity_log.split('\n')
        if len(lines) > 100:
            self.activity_log = '\n'.join(lines[-100:])
        
        # Always update display (shared log is always shown)
        self.error_log.setPlainText(self.activity_log)
        # Auto-scroll to bottom
        self.error_log.verticalScrollBar().setValue(
            self.error_log.verticalScrollBar().maximum()
        )
    
    def check_plc_connection(self):
        """Check PLC connection via ping"""
        if self.current_selected_station not in self.snap7_stations:
            QMessageBox.warning(self, 'Wrong Station', 'This station does not support Snap7 PLC connection!')
            return
        
        if self.current_selected_station == 'PLCSim Station':
            ip = self.plc_controller.get_simulator_ip()
        else:
            ip = self.current_selected_station.split('_')[1] if '_' in self.current_selected_station else None
            if not ip:
                QMessageBox.warning(self, 'Error', 'Cannot extract IP from station name!')
                return
        
        self.add_log(self.current_selected_station, f"Checking connection to {ip}...")
        
        try:
            result = subprocess.run(
                ['ping', '-n', '1', '-w', '1000', ip],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                self.plc_switch_enabled = True
                self.plc_connection_switch.setEnabled(True)
                self.plc_connection_status_label.setText(f'✓ {ip} reachable')
                self.plc_connection_status_label.setStyleSheet("color: #27ae60; font-size: 8pt; font-weight: bold;")
                self.add_log(self.current_selected_station, f"✓ Connection OK - {ip} is reachable")
                QMessageBox.information(self, 'Connection OK', f'PLC at {ip} is reachable!\nYou can now enable PLC connection.')
            else:
                self.plc_switch_enabled = False
                self.plc_connection_switch.setEnabled(False)
                self.plc_connection_switch.setChecked(False)
                self.plc_connection_status_label.setText(f'✗ {ip} not reachable')
                self.plc_connection_status_label.setStyleSheet("color: #e74c3c; font-size: 8pt; font-weight: bold;")
                self.add_log(self.current_selected_station, f"✗ ERROR: Cannot reach {ip}")
                QMessageBox.critical(self, 'Connection Failed', f'Cannot reach PLC at {ip}\n\nPlease check:\n- PLC is running\n- IP address is correct\n- Network connection')
        
        except subprocess.TimeoutExpired:
            self.plc_switch_enabled = False
            self.plc_connection_switch.setEnabled(False)
            self.plc_connection_switch.setChecked(False)
            self.plc_connection_status_label.setText(f'✗ Timeout')
            self.plc_connection_status_label.setStyleSheet("color: #e74c3c; font-size: 8pt; font-weight: bold;")
            self.add_log(self.current_selected_station, f"✗ ERROR: Timeout - No response from {ip}")
            QMessageBox.critical(self, 'Connection Timeout', f'No response from PLC at {ip}')
        
        except Exception as e:
            self.plc_switch_enabled = False
            self.plc_connection_switch.setEnabled(False)
            self.plc_connection_switch.setChecked(False)
            self.plc_connection_status_label.setText(f'✗ Error')
            self.plc_connection_status_label.setStyleSheet("color: #e74c3c; font-size: 8pt; font-weight: bold;")
            self.add_log(self.current_selected_station, f"✗ ERROR: {str(e)}")
            QMessageBox.critical(self, 'Connection Error', f'Error checking connection:\n{str(e)}')
    
    def on_plc_switch_changed(self, state):
        """Handle PLC connection switch toggle"""
        if state == Qt.Checked:
            if self.plc_controller.is_connected():
                return
            
            if self.current_selected_station == 'PLCSim Station':
                success, message = self.plc_controller.connect_plcsim()
            else:
                ip = self.current_selected_station.split('_')[1] if '_' in self.current_selected_station else None
                if not ip:
                    QMessageBox.critical(self, 'Error', 'Cannot extract IP from station name!')
                    self.plc_connection_switch.setChecked(False)
                    return
                
                rack = 0
                slot = 1
                if self.plc_controller.plc.connect(ip, rack, slot):
                    self.plc_controller.connected = True
                    success = True
                    message = f"Connected to {ip}"
                else:
                    success = False
                    message = f"Failed to connect to {ip}"
            
            if success:
                self.add_log(self.current_selected_station, f"✓ PLC connected - {message}")
                self.plc_connection_status_label.setText('✓ PLC Connected')
                self.plc_connection_status_label.setStyleSheet("color: #27ae60; font-size: 8pt; font-weight: bold;")
                
                success, msg = self.plc_controller.send_tag("Q64.0", 1, "Byte")
                if success:
                    print(f"PLC Switch ON -> QB64 = 1")
                    self.add_log(self.current_selected_station, "PLC Switch ON -> QB64 = 1")
                    self.plc_read_timer.start()
            else:
                self.plc_connection_switch.setChecked(False)
                self.plc_connection_status_label.setText(f'✗ Connection failed')
                self.plc_connection_status_label.setStyleSheet("color: #e74c3c; font-size: 8pt; font-weight: bold;")
                self.add_log(self.current_selected_station, f"✗ ERROR: PLC connection failed - {message}")
                QMessageBox.critical(self, 'Connection Failed', f'Failed to connect to PLC:\n{message}')
        else:
            if self.plc_controller.is_connected():
                success, msg = self.plc_controller.send_tag("Q64.0", 0, "Byte")
                if success:
                    print(f"PLC Switch OFF -> QB64 = 0")
                    self.add_log(self.current_selected_station, "PLC Switch OFF -> QB64 = 0")
                
                self.plc_read_timer.stop()
                self.plc_controller.disconnect_plcsim()
                self.add_log(self.current_selected_station, "PLC disconnected")
                self.plc_connection_status_label.setText('Disconnected')
                self.plc_connection_status_label.setStyleSheet("color: #7f8c8d; font-size: 8pt; font-style: italic;")
    
    def on_station_changed(self, index):
        """Handle station selection from left combo"""
        if index > 0:
            station = self.station_combo.currentText()
            self.load_station_tags(station)
            self.current_selected_station = station
            
            # Show IP edit button only when PLCSim Station is selected
            if station == 'PLCSim Station':
                self.simulator_ip_btn.setVisible(True)
            else:
                self.simulator_ip_btn.setVisible(False)
            
            # Restore progress bar value for this station
            progress = self.station_progress.get(station, 0)
            self.progress_bar.setValue(progress)
            
            # Update shared log display (always same for all stations)
            self.error_log.setPlainText(self.activity_log)
            self.error_log.verticalScrollBar().setValue(
                self.error_log.verticalScrollBar().maximum()
            )
            
            self.update_status_display(station)  # Update status for new station
    
    def toggle_connection(self):
        if self.connect_btn.text() == 'CAN Bus: OFF':
            if self.station_combo.currentIndex() <= 0:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle('Station Required')
                msg.setText('Please select a station first!')
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
                return
            
            station = self.station_combo.currentText()
            self.current_selected_station = station
            self.load_station_tags(station)
            
            # Create or update canbus_manager tag for this station
            if station not in self.tag_values:
                self.tag_values[station] = {}
            
            if 'canbus_manager' not in self.tag_values[station]:
                self.tag_values[station]['canbus_manager'] = {
                    'address': 'M0.0',
                    'db': '',
                    'type': 'bool',
                    'value': 'ON',
                    'display_format': 'DEC',
                    'sending_format': 'DEC'
                }
            else:
                self.tag_values[station]['canbus_manager']['value'] = 'ON'
            
            # Save to JSON
            self.save_tag_values()
            
            # Reload tags to show canbus_manager
            self.load_station_tags(station)
            
            # Mark this station as connected
            self.station_connections[station] = True
            
            # Log connection
            self.add_log(station, "CAN Bus connected - canbus_manager tag activated")
            
            # Update display for this station
            self.update_status_display(station)
            
            # Animate progress (dialog will show at 100%)
            self.animate_progress(station)
        else:
            station = self.current_selected_station
            
            # FIRST: Send 0 to QB64 when CAN Bus is turned OFF
            if station == 'PLCSim Station':
                if not self.plc_controller.is_connected():
                    success, message = self.plc_controller.connect_plcsim()
                    if success:
                        print(f"PLC Auto-connect: {message}")
                
                if self.plc_controller.is_connected():
                    success, msg = self.plc_controller.send_tag("Q64.0", 0, "Byte")
                    if success:
                        print(f"CAN Bus OFF -> QB64 = 0")
                        self.add_log(station, "CAN Bus OFF -> QB64 = 0")
                        self.plc_read_timer.stop()
                    else:
                        print(f"Failed to send QB64: {msg}")
            
            # SECOND: Reset progress bar immediately
            self.progress_bar.setValue(0)
            if station:
                self.station_progress[station] = 0
            
            # THIRD: Update canbus_manager tag value to OFF
            if station and station in self.tag_values:
                if 'canbus_manager' in self.tag_values[station]:
                    self.tag_values[station]['canbus_manager']['value'] = 'OFF'
                    self.save_tag_values()
            
            # FOURTH: Mark this station as disconnected
            if station:
                self.station_connections[station] = False
            
            # FIFTH: Log disconnection
            if station:
                self.add_log(station, "CAN Bus disconnected - canbus_manager tag deactivated")
            
            # SIXTH: Update display for this station
            self.update_status_display(station)
            
            # SEVENTH: Show disconnect confirmation dialog
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle('Disconnected')
            msg.setText('CAN Bus disconnected from PLC.')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
    
    def animate_progress(self, station):
        self.progress_value = 0
        self.current_connecting_station = station  # Store for dialog
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(30)
    
    def update_progress(self):
        self.progress_value += 2
        self.progress_bar.setValue(self.progress_value)
        
        # Save progress for current station
        if self.current_connecting_station:
            self.station_progress[self.current_connecting_station] = self.progress_value
        
        if self.progress_value >= 100:
            self.timer.stop()
            
            # Send 1 to QB64 when CAN Bus connection completes
            if self.current_connecting_station == 'PLCSim Station':
                if not self.plc_controller.is_connected():
                    success, message = self.plc_controller.connect_plcsim()
                    if success:
                        print(f"PLC Auto-connect: {message}")
                
                if self.plc_controller.is_connected():
                    success, msg = self.plc_controller.send_tag("Q64.0", 1, "Byte")
                    if success:
                        print(f"CAN Bus ON -> QB64 = 1")
                        self.add_log(self.current_connecting_station, "CAN Bus ON -> QB64 = 1")
                        self.plc_read_timer.start()
                    else:
                        print(f"Failed to send QB64: {msg}")
            
            # Show success dialog AFTER progress bar completes
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle('Connection Successful')
            msg.setText(f'CAN Bus connected to {self.current_connecting_station}!')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
    
    def read_plc_tags(self):
        """Periodically read all tags from PLC and update PLC Value column"""
        if self.current_selected_station not in self.snap7_stations:
            return
        
        if not self.plc_controller.is_connected():
            return
        
        for row in range(self.tag_table.rowCount()):
            address_item = self.tag_table.item(row, 1)
            type_item = self.tag_table.item(row, 2)
            plc_value_item = self.tag_table.item(row, 6)
            
            if not address_item or not address_item.text().strip():
                continue
            
            address = address_item.text().strip()
            data_type = type_item.text() if type_item else 'Byte'
            
            success, value, msg = self.plc_controller.read_tag(address, data_type)
            
            if success and plc_value_item:
                self.tag_table.blockSignals(True)
                plc_value_item.setText(str(value))
                self.tag_table.blockSignals(False)
    
    def update_status_display(self, station):
        """Update PLC and CAN Bus status display for current station"""
        is_connected = self.station_connections.get(station, False)
        
        if is_connected:
            self.plc_status_label.setText('\u25cf Connected')
            self.plc_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            self.can_status_label.setText('\u25cf Active')
            self.can_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            ip = station.split('_')[1] if '_' in station else 'localhost'
            self.ip_label.setText(f'IP: {ip}\nStation: {station}')
            
            # Button should show "ON"
            self.connect_btn.setText('CAN Bus: ON')
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 10pt;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
            """)
        else:
            self.plc_status_label.setText('\u25cf Disconnected')
            self.plc_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
            self.can_status_label.setText('\u25cf Inactive')
            self.can_status_label.setStyleSheet("color: #95a5a6; font-weight: bold;")
            
            self.ip_label.setText('IP: -')
            
            # Button should show "OFF"
            self.connect_btn.setText('CAN Bus: OFF')
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 10pt;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
                QPushButton:pressed {
                    background-color: #6c7a7d;
                }
            """)
    
    def load_station_tags(self, station):
        if not station or station == 'Select...':
            return
        
        self.tag_table.setRowCount(0)
        self._old_tag_names.clear()
        
        all_tags = {}
        
        if station in self.tag_values:
            for tag_name, stored_tag in self.tag_values[station].items():
                if not tag_name or not tag_name.strip():
                    continue
                    
                if isinstance(stored_tag, dict):
                    all_tags[tag_name] = {
                        'address': str(stored_tag.get('address', '')),
                        'db': str(stored_tag.get('db', '')),
                        'type': stored_tag.get('type', 'real'),
                        'value': stored_tag.get('value', '-'),
                        'display_format': stored_tag.get('display_format', 'DEC'),
                        'sending_format': stored_tag.get('sending_format', 'DEC')
                    }
        
        self.tag_table.setRowCount(len(all_tags))
        
        row = 0
        for tag_name, tag_data in all_tags.items():
            self._old_tag_names[row] = tag_name
            
            name_item = QTableWidgetItem(tag_name)
            name_item.setFont(QFont('Arial', 9))
            self.tag_table.setItem(row, 0, name_item)
            
            addr_item = QTableWidgetItem(tag_data['address'])
            addr_item.setFont(QFont('Arial', 9))
            self.tag_table.setItem(row, 1, addr_item)
            
            type_item = QTableWidgetItem(tag_data['type'])
            type_item.setFont(QFont('Arial', 9))
            self.tag_table.setItem(row, 2, type_item)
            
            display_fmt = tag_data.get('display_format', 'DEC')
            formatted_value = self.format_value(tag_data['value'], display_fmt)
            value_item = QTableWidgetItem(formatted_value)
            value_item.setFont(QFont('Arial', 9))
            self.tag_table.setItem(row, 3, value_item)
            
            display_format_item = QTableWidgetItem(display_fmt)
            display_format_item.setFont(QFont('Arial', 9))
            self.tag_table.setItem(row, 4, display_format_item)
            
            sending_fmt = tag_data.get('sending_format', 'DEC')
            sending_format_item = QTableWidgetItem(sending_fmt)
            sending_format_item.setFont(QFont('Arial', 9))
            self.tag_table.setItem(row, 5, sending_format_item)
            
            plc_value_item = QTableWidgetItem('-')
            plc_value_item.setFont(QFont('Arial', 9))
            plc_value_item.setFlags(plc_value_item.flags() & ~Qt.ItemIsEditable)
            self.tag_table.setItem(row, 6, plc_value_item)
            
            status_item = QTableWidgetItem('⏳')
            status_item.setFont(QFont('Arial', 9))
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            self.tag_table.setItem(row, 7, status_item)
            
            force_btn = QPushButton('▶')
            force_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
            """)
            force_btn.setFixedSize(50, 28)
            force_btn.clicked.connect(lambda checked, r=row, t=tag_name: self.on_force_value(r, t))
            self.tag_table.setCellWidget(row, 8, force_btn)
            
            delete_btn = QPushButton('✕')
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
                QPushButton:pressed {
                    background-color: #a93226;
                }
            """)
            delete_btn.setFixedSize(50, 28)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_tag_row(r))
            self.tag_table.setCellWidget(row, 9, delete_btn)
            
            row += 1
        
        self.tag_table.resizeRowsToContents()
    
    def load_tag_values(self):
        if os.path.exists(self.tag_values_file):
            try:
                with open(self.tag_values_file, 'r') as f:
                    self.tag_values = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.tag_values = {}
        else:
            self.tag_values = {}
    
    def load_config(self):
        """Load PLC configuration (Simulator IP, etc.)"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.plc_config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.plc_config = {}
        
        # Set default Simulator IP if not exists
        if 'simulator_ip' not in self.plc_config:
            self.plc_config['simulator_ip'] = '10.76.106.152'
            self.save_config()
    
    def save_config(self):
        """Save PLC configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.plc_config, f, indent=4)
        except IOError:
            pass
    
    def save_tag_values(self):
        try:
            # Clean up empty tags before saving
            cleaned_tags = {}
            for station, tags in self.tag_values.items():
                cleaned_tags[station] = {}
                for tag_name, tag_data in tags.items():
                    # Skip tags with empty names or empty addresses
                    if tag_name and tag_name.strip() != '':
                        if isinstance(tag_data, dict):
                            address = tag_data.get('address', '')
                            if address and address.strip() != '':
                                cleaned_tags[station][tag_name] = tag_data
            
            with open(self.tag_values_file, 'w') as f:
                json.dump(cleaned_tags, f, indent=4)
        except IOError:
            pass
    
    def update_tag_value(self, station, tag_name, value):
        if station not in self.tag_values:
            self.tag_values[station] = {}
        self.tag_values[station][tag_name] = value
        self.save_tag_values()
    
    def on_tag_value_changed(self, item):
        row = self.tag_table.row(item)
        col = self.tag_table.column(item)
        
        if not self.current_selected_station:
            return
        
        tag_name_item = self.tag_table.item(row, 0)
        if not tag_name_item:
            return
        
        tag_name = tag_name_item.text().strip()
        
        if not tag_name:
            return
        
        old_tag_name = self._old_tag_names.get(row, tag_name)
        
        if self.current_selected_station not in self.tag_values:
            self.tag_values[self.current_selected_station] = {}
        
        if col == 0 and old_tag_name and old_tag_name != tag_name:
            if old_tag_name in self.tag_values[self.current_selected_station]:
                self.tag_values[self.current_selected_station][tag_name] = self.tag_values[self.current_selected_station].pop(old_tag_name)
            else:
                self.tag_values[self.current_selected_station][tag_name] = {
                    'db': '',
                    'address': '',
                    'type': 'real',
                    'value': '-',
                    'display_format': 'DEC',
                    'sending_format': 'DEC'
                }
            self._old_tag_names[row] = tag_name
            print(f"Tag renamed: '{old_tag_name}' → '{tag_name}' (not saved yet)")
            self.has_unsaved_changes = True
            return
        
        if tag_name not in self.tag_values[self.current_selected_station]:
            self.tag_values[self.current_selected_station][tag_name] = {
                'db': '',
                'address': '',
                'type': 'real',
                'value': '-',
                'display_format': 'DEC',
                'sending_format': 'DEC'
            }
            if tag_name:
                self.add_log(self.current_selected_station, f"Tag '{tag_name}' added")
            self.has_unsaved_changes = True
            self.save_tag_values()
            return
        
        new_value = item.text()
        
        if col == 1:
            # Address column
            if not new_value or new_value.strip() == '':
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle('Invalid Input')
                msg.setText('Address cannot be empty!')
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
                item.setText(self.tag_values[self.current_selected_station][tag_name].get('address', ''))
                return
            self.tag_values[self.current_selected_station][tag_name]['address'] = new_value
            # Only log if tag_name is not empty
            if tag_name and tag_name.strip() != '':
                self.add_log(self.current_selected_station, f"Tag '{tag_name}' address changed to '{new_value}'")
        elif col == 2:
            self.tag_values[self.current_selected_station][tag_name]['type'] = new_value
        elif col == 3:
            self.tag_values[self.current_selected_station][tag_name]['value'] = new_value
            display_fmt = self.tag_values[self.current_selected_station][tag_name].get('display_format', 'DEC')
            formatted_value = self.format_value(new_value, display_fmt)
            
            plc_value_item = self.tag_table.item(row, 6)
            if plc_value_item and plc_value_item.text() and plc_value_item.text() != '-':
                self.tag_table.blockSignals(True)
                plc_value_item.setText(self.format_value(plc_value_item.text(), 'Bin'))
                self.tag_table.blockSignals(False)
            
            # Only log if tag_name is not empty
            if tag_name and tag_name.strip() != '':
                self.add_log(self.current_selected_station, f"Tag '{tag_name}' value changed to '{new_value}'")
            
        elif col == 4:
            self.tag_values[self.current_selected_station][tag_name]['display_format'] = new_value
            
            value_item = self.tag_table.item(row, 3)
            if value_item:
                formatted_value = self.format_value(value_item.text(), new_value)
                self.tag_table.blockSignals(True)
                value_item.setText(formatted_value)
                self.tag_table.blockSignals(False)
            
            plc_value_item = self.tag_table.item(row, 6)
            if plc_value_item and plc_value_item.text() and plc_value_item.text() != '-':
                formatted_plc = self.format_value(plc_value_item.text(), 'Bin')
                self.tag_table.blockSignals(True)
                plc_value_item.setText(formatted_plc)
                self.tag_table.blockSignals(False)
            
            print(f"Display Format changed to: {new_value}")
            
        elif col == 5:
            self.tag_values[self.current_selected_station][tag_name]['sending_format'] = new_value
            print(f"Sending Format changed to: {new_value}")
        
        # Check if tag is incomplete (name without address or vice versa)
        # If so, remove it from memory since we won't save incomplete tags
        if tag_name in self.tag_values[self.current_selected_station]:
            address = self.tag_values[self.current_selected_station][tag_name].get('address', '').strip()
            if not address:  # Address is empty, remove this incomplete tag
                del self.tag_values[self.current_selected_station][tag_name]
        
        self.has_unsaved_changes = True
        self.save_tag_values()  # Auto-save on every change
    
    def save_tag_changes(self):
        self.save_tag_values()
        self.has_unsaved_changes = False
        print(f"✓ All changes saved to {self.tag_values_file}")
        self.show_save_success_dialog()
    
    def show_save_success_dialog(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('Save Successful')
        msg.setText('All changes have been saved successfully!')
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def show_save_info(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('Save Information')
        msg.setText(
            'Tag Saving Rules:\n\n'
            '• Tags must have BOTH Name AND Address to be saved\n'
            '• Tags with empty Name or empty Address will NOT be saved\n'
            '• Incomplete tags will be automatically removed from memory\n'
            '• Use the Delete button (✕) to remove unwanted tags\n\n'
            'When you close the application:\n'
            '• Empty or incomplete tags will be rejected\n'
            '• Only complete tags will be saved to file'
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def edit_simulator_ip(self):
        """Open dialog to edit PLCSim Station IP address"""
        from PyQt5.QtWidgets import QInputDialog, QLineEdit
        
        current_ip = self.plc_config.get('simulator_ip', '10.76.106.152')
        
        ip, ok = QInputDialog.getText(
            self,
            'Edit PLCSim IP',
            'Enter PLCSim Station IP Address:',
            QLineEdit.Normal,
            current_ip
        )
        
        if ok and ip.strip():
            # Basic IP validation
            parts = ip.strip().split('.')
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                self.plc_config['simulator_ip'] = ip.strip()
                self.save_config()
                
                QMessageBox.information(
                    self,
                    'Success',
                    f'PLCSim Station IP updated to: {ip.strip()}\n\nThis setting will be saved for future sessions.'
                )
            else:
                QMessageBox.warning(
                    self,
                    'Invalid IP',
                    'Please enter a valid IP address (e.g., 192.168.1.100)'
                )
    
    def on_force_value(self, row, tag_name):
        if not self.current_selected_station:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle('Station Required')
            msg.setText('Please select a station first!')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        
        # Validation: tag_name and address not empty
        tag_name_item = self.tag_table.item(row, 0)
        address_item = self.tag_table.item(row, 1)
        
        if not tag_name_item or not tag_name_item.text() or tag_name_item.text().strip() == '':
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle('Invalid Tag')
            msg.setText('Tag Name cannot be empty!')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        
        if not address_item or not address_item.text() or address_item.text().strip() == '':
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle('Invalid Address')
            msg.setText('Address cannot be empty!')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        
        value_item = self.tag_table.item(row, 3)
        if value_item:
            value_to_send = value_item.text()
            
            sending_format_item = self.tag_table.item(row, 5)
            sending_format = sending_format_item.text() if sending_format_item else 'DEC'
            
            formatted_send_value = self.format_value(value_to_send, sending_format)
            
            # Get address and type from table
            address = address_item.text()
            type_item = self.tag_table.item(row, 2)
            data_type = type_item.text() if type_item else 'Byte'
            
            if self.current_selected_station in self.snap7_stations:
                if not self.plc_controller.is_connected():
                    if self.current_selected_station == 'PLCSim Station':
                        success, message = self.plc_controller.connect_plcsim()
                    else:
                        ip = self.current_selected_station.split('_')[1] if '_' in self.current_selected_station else None
                        if ip:
                            rack = 0
                            slot = 1
                            if self.plc_controller.plc.connect(ip, rack, slot):
                                self.plc_controller.connected = True
                                success = True
                                message = f"Connected to {ip}"
                            else:
                                success = False
                                message = f"Failed to connect to {ip}"
                        else:
                            success = False
                            message = "Cannot extract IP"
                    
                    if not success:
                        QMessageBox.critical(self, 'PLC Connection Error', f'Cannot connect to PLC:\n{message}')
                        return
                
                try:
                    int_value = int(value_to_send)
                except ValueError:
                    QMessageBox.warning(self, 'Invalid Value', f'Value must be numeric: {value_to_send}')
                    return
                
                success, send_message = self.plc_controller.send_tag(address, int_value, data_type)
                
                print(f"PLC Send: {tag_name} -> {address} = {int_value} [{data_type}] - {'OK' if success else 'FAILED'}")
                
                status_item = self.tag_table.item(row, 7)
                if status_item:
                    self.tag_table.blockSignals(True)
                    status_item.setText('✓' if success else '✗')
                    self.tag_table.blockSignals(False)
                
                status_emoji = '✓' if success else '✗'
                self.add_log(self.current_selected_station, f"{status_emoji} {tag_name} -> {address} = {int_value}")
                
                if not success:
                    QMessageBox.warning(self, 'Send Failed', send_message)
            
            else:
                print(f"Force: {tag_name} -> {address} = {formatted_send_value}")
                self.add_log(self.current_selected_station, f"{tag_name} set to {formatted_send_value}")
                
                status_item = self.tag_table.item(row, 7)
                if status_item:
                    self.tag_table.blockSignals(True)
                    status_item.setText('✓')
                    self.tag_table.blockSignals(False)
    
    def closeEvent(self, event):
        # Check for empty tags (incomplete entries)
        has_empty_tags = False
        for row in range(self.tag_table.rowCount()):
            tag_name_item = self.tag_table.item(row, 0)
            address_item = self.tag_table.item(row, 1)
            
            tag_name = tag_name_item.text().strip() if tag_name_item else ''
            address = address_item.text().strip() if address_item else ''
            
            if (tag_name and not address) or (not tag_name and address):
                has_empty_tags = True
                break
        
        if has_empty_tags:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle('Incomplete Tags')
            msg.setText('Please fill in all tag names and addresses before exiting. Remove incomplete tags first.')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            event.ignore()
            return
        
        reply = QMessageBox.question(
            self,
            'Exit',
            'Do you want to exit the application?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.save_tag_values()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle('Saved')
            msg.setText('All data has been saved. Exiting application...')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            event.accept()
        else:
            event.ignore()
    
    def add_new_tag_row(self):
        if not self.current_selected_station:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle('Station Required')
            msg.setText('Please select a station first!')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        
        current_row = self.tag_table.rowCount()
        self.tag_table.insertRow(current_row)
        
        name_item = QTableWidgetItem('')
        name_item.setFont(QFont('Arial', 9))
        self.tag_table.setItem(current_row, 0, name_item)
        
        addr_item = QTableWidgetItem('')
        addr_item.setFont(QFont('Arial', 9))
        self.tag_table.setItem(current_row, 1, addr_item)
        
        type_item = QTableWidgetItem('Bool')
        type_item.setFont(QFont('Arial', 9))
        self.tag_table.setItem(current_row, 2, type_item)
        
        value_item = QTableWidgetItem('-')
        value_item.setFont(QFont('Arial', 9))
        self.tag_table.setItem(current_row, 3, value_item)
        
        display_format_item = QTableWidgetItem('DEC')
        display_format_item.setFont(QFont('Arial', 9))
        self.tag_table.setItem(current_row, 4, display_format_item)
        
        sending_format_item = QTableWidgetItem('DEC')
        sending_format_item.setFont(QFont('Arial', 9))
        self.tag_table.setItem(current_row, 5, sending_format_item)
        
        plc_value_item = QTableWidgetItem('-')
        plc_value_item.setFont(QFont('Arial', 9))
        plc_value_item.setFlags(plc_value_item.flags() & ~Qt.ItemIsEditable)
        self.tag_table.setItem(current_row, 6, plc_value_item)
        
        status_item = QTableWidgetItem('⏳')
        status_item.setFont(QFont('Arial', 9))
        status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
        self.tag_table.setItem(current_row, 7, status_item)
        
        force_btn = QPushButton('▶')
        force_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        force_btn.setFixedSize(50, 28)
        force_btn.clicked.connect(lambda checked, r=current_row: self.on_force_value(r, self.tag_table.item(r, 0).text() if self.tag_table.item(r, 0) else ''))
        self.tag_table.setCellWidget(current_row, 8, force_btn)
        
        delete_btn = QPushButton('✕')
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        delete_btn.setFixedSize(50, 28)
        delete_btn.clicked.connect(lambda checked, r=current_row: self.delete_tag_row(r))
        self.tag_table.setCellWidget(current_row, 9, delete_btn)
        
        self.tag_table.scrollToItem(self.tag_table.item(current_row, 0))
        self.has_unsaved_changes = True
        print(f"Added new tag row at index {current_row}")
    
    def delete_tag_row(self, row):
        tag_name_item = self.tag_table.item(row, 0)
        tag_name = tag_name_item.text().strip() if tag_name_item else ''
        
        if self.current_selected_station and tag_name:
            if self.current_selected_station in self.tag_values:
                if tag_name in self.tag_values[self.current_selected_station]:
                    del self.tag_values[self.current_selected_station][tag_name]
                    self.save_tag_values()
                    self.add_log(self.current_selected_station, f"Tag '{tag_name}' deleted")
        
        self.tag_table.removeRow(row)
        self.has_unsaved_changes = True
    
    def toggle_sidebar(self):
        """Toggle left sidebar visibility"""
        if self.left_panel.isVisible():
            self.left_panel.hide()
        else:
            self.left_panel.show()
    
    def format_value(self, value, display_format):
        if not value or value == '-':
            return '-'
        
        try:
            if isinstance(value, str):
                val = value.strip()
                if val.startswith('0x') or val.startswith('0X'):
                    num = int(val, 16)
                elif val.startswith('0b') or val.startswith('0B'):
                    num = int(val, 2)
                else:
                    num = int(float(val))
            else:
                num = int(value)
            
            if display_format == 'DEC/J' or display_format == 'DEC':
                return str(num)
            elif display_format == 'Hex':
                return f'0x{num:X}'
            elif display_format == 'Bin':
                return f'0b{num:b}'
            elif display_format == 'Octal':
                return f'0o{num:o}'
            elif display_format == 'BCD':
                return f'0x{num:02X}'
            elif display_format in ['Character', 'Unicode character']:
                if 0 <= num <= 127:
                    return chr(num)
                else:
                    return str(num)
            else:
                return str(num)
        
        except (ValueError, TypeError):
            return value

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = TIAPortalGUI()
    gui.show()
    sys.exit(app.exec_())
