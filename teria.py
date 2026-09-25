import sys
import os
import json
import winreg
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QGridLayout, QSlider, QCheckBox
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen

APP_NAME = "BatteryWidget2x6"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".battery_widget_config.json")

def load_settings():
    """Carica posizione, opacità e turno corrente da file JSON locale."""
    settings = {"x": 100, "y": 100, "opacity": 255, "turn": 0}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.loadf() if hasattr(json, 'loadf') else json.load(f)
                settings.update(data)
        except Exception as e:
            print(f"Errore lettura configurazione: {e}")
    return settings

def save_settings(x, y, opacity, turn):
    """Salva immediatamente stato e posizione su file JSON."""
    data = {
        "x": int(x),
        "y": int(y),
        "opacity": int(opacity),
        "turn": int(turn)
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Errore salvataggio configurazione: {e}")

def get_startup_status():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

def set_startup_status(enable):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        if enable:
            script_path = os.path.abspath(sys.argv[0])
            python_path = sys.executable.replace("python.exe", "pythonw.exe")
            command = f'"{python_path}" "{script_path}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Errore gestione avvio automatico: {e}")

class BatteryWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Carica le preferenze salvate
        saved = load_settings()
        self.current_turn = saved["turn"]
        self.bg_alpha = saved["opacity"]
        self.initial_pos = QPoint(saved["x"], saved["y"])
        
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(380, 260)
        self.move(self.initial_pos)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 4, 10, 10)
        main_layout.setSpacing(8)

        # 1. Barra del titolo personalizzata (trascinabile)
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)
        
        indicator = QLabel("●")
        indicator.setStyleSheet("color: #10b981; font-size: 14px;")
        
        title_label = QLabel("Battery Widget (2x6)")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(239, 68, 68, 0.8); color: white; border-radius: 4px; font-weight: bold; border: none; }
            QPushButton:hover { background: #dc2626; }
        """)
        close_btn.clicked.connect(self.close)

        title_bar.addWidget(indicator)
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        title_bar.addWidget(close_btn)
        main_layout.addLayout(title_bar)

        # 2. Griglia 2x6 delle batterie
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(6)
        main_layout.addLayout(self.grid_layout)

        # 3. Controlli avanzati (Opacità e Checkbox Windows Startup)
        settings_layout = QHBoxLayout()
        
        opacity_label = QLabel("Opacità:")
        opacity_label.setFont(QFont("Segoe UI", 8))
        opacity_label.setStyleSheet("color: rgba(255,255,255,0.7);")
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(self.bg_alpha)
        self.opacity_slider.setFixedWidth(90)
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: rgba(255,255,255,0.2); border-radius: 2px; }
            QSlider::handle:horizontal { background: #3b82f6; width: 12px; margin: -4px 0; border-radius: 6px; }
        """)
        self.opacity_slider.valueChanged.connect(self.change_opacity)

        self.startup_chk = QCheckBox("Avvia con Windows")
        self.startup_chk.setFont(QFont("Segoe UI", 8))
        self.startup_chk.setStyleSheet("color: rgba(255,255,255,0.8); spacing: 5px;")
        self.startup_chk.setChecked(get_startup_status())
        self.startup_chk.toggled.connect(set_startup_status)

        settings_layout.addWidget(opacity_label)
        settings_layout.addWidget(self.opacity_slider)
        settings_layout.addStretch()
        settings_layout.addWidget(self.startup_chk)
        
        main_layout.addLayout(settings_layout)

        # 4. Controlli di Navigazione Principali (Indietro, Avanti trasparenti)
        controls_layout = QHBoxLayout()
        
        self.prev_btn = self.create_transparent_button("Indietro", self.prev_step)
        self.next_btn = self.create_transparent_button("Avanti", self.next_step)

        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.next_btn)
        
        main_layout.addLayout(controls_layout)

        self.setLayout(main_layout)
        self.update_grid()

    def create_transparent_button(self, text, callback):
        btn = QPushButton(text)
        btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        btn.setStyleSheet("""
            QPushButton { 
                background: rgba(255, 255, 255, 0.08); 
                color: white; 
                border-radius: 6px; 
                padding: 6px 14px; 
                border: 1px solid rgba(255, 255, 255, 0.2); 
            }
            QPushButton:hover { 
                background: rgba(255, 255, 255, 0.15); 
                border: 1px solid rgba(255, 255, 255, 0.35);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.25);
            }
        """)
        btn.clicked.connect(callback)
        return btn

    def change_opacity(self, value):
        self.bg_alpha = value
        self.update()
        self.save_current_state()  # Salvataggio istantaneo quando sposti lo slider

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bg_color = QColor(15, 23, 42, self.bg_alpha)
        border_color = QColor(255, 255, 255, int(self.bg_alpha * 0.2))
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1))
        
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)

    def update_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        next_col = self.current_turn % 6
        empty_col1 = (self.current_turn + 4) % 6
        empty_col2 = (self.current_turn + 5) % 6

        for c in range(6):
            if c == next_col:
                type_slot = "next"
                label_top = "Next"
                label_bottom = "Next"
            elif c == empty_col1 or c == empty_col2:
                type_slot = "empty"
                label_top = "Vuoto"
                label_bottom = "Vuoto"
            else:
                type_slot = "active"
                label_top = "Cariche"
                label_bottom = "Cariche"

            self.grid_layout.addWidget(self.create_cell_widget(type_slot, label_top, f"S{c+1}"), 0, c)
            self.grid_layout.addWidget(self.create_cell_widget(type_slot, label_bottom, f"I{c+1}"), 1, c)

    def create_cell_widget(self, type_slot, label, slot_id):
        cell = QWidget()
        cell.setFixedHeight(50)
        
        if type_slot == "empty":
            bg = "background: rgba(30, 41, 59, 0.8); border: 2px dashed rgba(156, 163, 175, 0.6);"
            text_color = "#9ca3af"
        elif type_slot == "next":
            bg = "background: rgba(16, 185, 129, 0.35); border: 2px solid #10b981;"
            text_color = "#34d399"
        else:
            bg = "background: rgba(59, 130, 246, 0.35); border: 2px solid #3b82f6;"
            text_color = "#60a5fa"

        cell.setStyleSheet(f"""
            QWidget {{
                {bg}
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        id_lbl = QLabel(slot_id)
        id_lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        id_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.7); border: none; background: transparent;")
        id_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_lbl = QLabel(label)
        text_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        text_lbl.setStyleSheet(f"color: {text_color}; border: none; background: transparent;")
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(id_lbl)
        layout.addWidget(text_lbl)
        cell.setLayout(layout)
        return cell

    def next_step(self):
        self.current_turn = (self.current_turn + 1) % 6
        self.update_grid()
        self.save_current_state()

    def prev_step(self):
        self.current_turn = (self.current_turn - 1) % 6
        self.update_grid()
        self.save_current_state()

    def save_current_state(self):
        pos = self.pos()
        save_settings(pos.x(), pos.y(), self.bg_alpha, self.current_turn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
            self.save_current_state()  # Salva posizione in tempo reale mentre trascini la finestra

    def closeEvent(self, event):
        self.save_current_state()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = BatteryWidget()
    widget.show()
    sys.exit(app.exec())