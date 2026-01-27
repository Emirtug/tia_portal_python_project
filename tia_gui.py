import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont

class TIAPortalGUI(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.setWindowTitle('TIA Portal Kontrol Lab Uygulamasi')
        self.setGeometry(100, 100, 800, 600)
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana vertical layout (content + footer)
        main_vertical_layout = QVBoxLayout()
        central_widget.setLayout(main_vertical_layout)
        
        # Content horizontal layout
        main_layout = QHBoxLayout()
        
        # SOL PANEL - İstasyon Seçimi
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e0e0e0;")
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        station_label = QLabel('Station Selection')
        station_label.setStyleSheet("font-size: 14px; color: #1a1a1a; margin: 20px; font-weight: bold;")
        left_layout.addWidget(station_label)
        
        # Station Dropdown
        self.station_combo = QComboBox()
        stations = [
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
            'Simulator_localhost',
        ]
        
        self.station_combo.addItems(stations)
        self.station_combo.currentTextChanged.connect(self.on_station_selected)
        left_layout.addWidget(self.station_combo)
        
        left_layout.addStretch()
        
        # Connection Status Panel
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 4px; padding: 10px;")
        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(8, 8, 8, 8)
        status_layout.setSpacing(5)
        
        status_title = QLabel('Connection Status')
        status_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #1a1a1a;")
        status_layout.addWidget(status_title)
        
        self.status_indicator = QLabel('● Disconnected')
        self.status_indicator.setStyleSheet("font-size: 12px; color: #ff6b6b; font-weight: bold;")
        status_layout.addWidget(self.status_indicator)
        
        self.ip_label = QLabel('IP: -')
        self.ip_label.setStyleSheet("font-size: 11px; color: #555;")
        status_layout.addWidget(self.ip_label)
        
        status_frame.setLayout(status_layout)
        left_layout.addWidget(status_frame)
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(250)
        
        # ANA İÇERİK ALANI (sağ taraf)
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #fafafa;")
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(30, 30, 30, 30)
        right_layout.setSpacing(20)
        
        # PLC Logo/Icon
        plc_logo = QLabel()
        plc_logo.setText("Siemens PLC Connection")
        plc_logo.setStyleSheet("font-size: 24px; text-align: center;")
        plc_logo.setAlignment(Qt.AlignCenter)
        
        self.content_label = QLabel('Select Station')
        self.content_label.setStyleSheet("font-size: 14px; color: #1a1a1a; margin: 20px; font-weight: bold;")
        right_layout.addWidget(plc_logo)
        right_layout.addWidget(self.content_label)
        right_layout.addStretch()
        right_panel.setLayout(right_layout)
        
        # Ana layout'a ekle
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
        
        # FOOTER PANEL
        footer_panel = QFrame()
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(10, 5, 10, 5)
        
        footer_label = QLabel('© 2026 Control Lab - Developed by: Emirtug Kacar')
        footer_label.setStyleSheet("font-size: 12px; color: #1a1a1a; font-weight: bold;")
        footer_layout.addStretch()
        footer_layout.addWidget(footer_label)
        footer_panel.setLayout(footer_layout)
        footer_panel.setStyleSheet("background-color: #d3d3d3; border-top: 1px solid #bbb;")
        footer_panel.setMaximumHeight(30)
        
        # Main vertical layout'a ekle
        main_vertical_layout.addLayout(main_layout)
        main_vertical_layout.addWidget(footer_panel)
        
        self.show()
    
    def on_station_selected(self, station):
        if station == 'Select...':
            self.content_label.setText('Select Station')
            self.status_indicator.setText('● Disconnected')
            self.status_indicator.setStyleSheet("font-size: 12px; color: #ff6b6b; font-weight: bold;")
            self.ip_label.setText('IP: -')
        else:
            self.content_label.setText(f'Connected Station: {station}')
            self.status_indicator.setText('● Connected')
            self.status_indicator.setStyleSheet("font-size: 12px; color: #27ae60; font-weight: bold;")
            self.ip_label.setText(f'IP: {station.split("_")[1]}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = TIAPortalGUI()
    sys.exit(app.exec_())
