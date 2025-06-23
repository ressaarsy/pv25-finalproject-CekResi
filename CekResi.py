import sys
import sqlite3
from datetime import datetime
import requests
from fpdf import FPDF
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QAction, QFileDialog, QStatusBar
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTimer

API_KEY = "d2dfaff50763114b0cb3b6595b31bd5eda28245b5e3f5fc2e411e212ec6e0e29"
API_URL = "https://api.binderbyte.com/v1/track"
DB_NAME = "riwayat_resi.db"

EKSPEDISI_MAP = {
    "JNE Express": "jne",
    "J&T Express": "jnt",
    "SiCepat Express": "sicepat",
    "AnterAja": "anteraja",
    "POS Indonesia": "pos",
    "Wahana Express": "wahana",
    "Lion Parcel": "lion",
    "Ninja Xpress": "ninja",
    "SAP Express": "sap",
    "JET Express": "jet",
    "REX Kiriman Cepat": "rex",
    "IDL Cargo": "idl",
    "First Logistics": "first",
    "Shopee Express": "spx"
}

class CekResiFinal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("\U0001F4E6 Lacakin - Cek Semua Resimu")
        self.setGeometry(200, 200, 800, 540)
        self.setWindowIcon(QIcon("box_icon.png"))

        self.mode = "light"
        self._buat_database()
        self._buat_widget()
        self._buat_menu()
        self._buat_statusbar()
        self._atur_style("light")

    def _atur_style(self, mode="light"):
        if mode == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #121212;
                    color: #f0f0f0;
                }
                QLabel {
                    color: #f0f0f0;
                    font-family: 'Segoe UI';
                    font-size: 12pt;
                }
                QPushButton {
                    background-color: #1e88e5;
                    color: white;
                    border-radius: 6px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
                QLineEdit, QComboBox {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 6px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    selection-background-color: #3a3a3a;
                    selection-color: white;
                }
                QTableWidget {
                    background-color: #1e1e1e;
                    color: #f0f0f0;
                    gridline-color: #555;
                }
                QHeaderView::section {
                    background-color: #333;
                    color: white;
                    font-weight: bold;
                }
                QStatusBar {
                    background-color: #222;
                    color: #f0f0f0;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f7fa;
                }
                QLabel {
                    font-family: 'Segoe UI';
                    font-size: 12pt;
                    color: #003366;
                }
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border-radius: 6px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background-color: #005a9e;
                }
                QLineEdit, QComboBox {
                    padding: 6px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background-color: white;
                    color: black;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: black;
                    selection-background-color: #cce6ff;
                    selection-color: black;
                }
                QTableWidget {
                    background-color: white;
                    color: black;
                }
                QHeaderView::section {
                    background-color: #e0e0e0;
                    color: black;
                    font-weight: bold;
                }
                QStatusBar {
                    background-color: #e0e0e0;
                }
            """)

    def _buat_widget(self):
        self.wadah = QWidget()
        self.setCentralWidget(self.wadah)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Baris atas: judul + tombol mode
        baris_atas = QHBoxLayout()

        judul = QLabel("\U0001F4E6 Ayo Lacak Paketmu!")
        judul.setFont(QFont("Segoe UI", 18, QFont.Bold))
        judul.setAlignment(Qt.AlignCenter)

        baris_atas.addWidget(judul, alignment=Qt.AlignLeft)
        baris_atas.addStretch()

        self.btn_mode = QPushButton("🌙")
        self.btn_mode.setFixedSize(40, 30)
        self.btn_mode.setToolTip("Ubah Mode Gelap/Terang")
        self.btn_mode.clicked.connect(self._toggle_mode)

        baris_atas.addWidget(self.btn_mode, alignment=Qt.AlignRight)
        layout.addLayout(baris_atas)

        deskripsi = QLabel("Pantau perjalanan paket dari berbagai ekspedisi di Indonesia secara mudah dan cepat.")
        deskripsi.setAlignment(Qt.AlignCenter)
        deskripsi.setStyleSheet("font-size: 10pt; margin-bottom: 10px;")
        layout.addWidget(deskripsi)

        form = QHBoxLayout()
        self.in_resi = QLineEdit()
        self.in_resi.setPlaceholderText("Nomor Resi")
        self.in_kurir = QComboBox()
        self.in_kurir.addItems(EKSPEDISI_MAP.keys())
        self.in_catatan = QLineEdit()
        self.in_catatan.setPlaceholderText("Catatan opsional")

        btn_cek = QPushButton("\U0001F50E Cek Resi")
        btn_cek.clicked.connect(self._cek_resi)

        form.addWidget(QLabel("Resi:"))
        form.addWidget(self.in_resi)
        form.addWidget(QLabel("Kurir:"))
        form.addWidget(self.in_kurir)
        form.addWidget(btn_cek)

        layout.addLayout(form)
        layout.addWidget(self.in_catatan)

        self.tabel = QTableWidget()
        self.tabel.setColumnCount(2)
        self.tabel.setHorizontalHeaderLabels(["Tanggal", "Keterangan"])
        self.tabel.setColumnWidth(0, 200)
        self.tabel.setColumnWidth(1, 520)
        self.tabel.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        layout.addWidget(self.tabel)

        layout.addStretch()
        self.wadah.setLayout(layout)

    def _buat_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        ekspor_pdf = QAction("Ekspor ke PDF", self)
        ekspor_pdf.triggered.connect(self._ekspor_pdf)
        file_menu.addAction(ekspor_pdf)

        keluar = QAction("Keluar", self)
        keluar.triggered.connect(self.close)
        file_menu.addAction(keluar)

        help_menu = menu.addMenu("Help")
        tentang = QAction("Tentang", self)
        tentang.triggered.connect(self._tampil_tentang)
        help_menu.addAction(tentang)

    def _tampil_tentang(self):
        teks = (
            "<b>\U0001F4E6 Lacakin - Cek Semua Resimu</b><br><br>"
            "Versi Aplikasi: 1.0.0<br><br>"
            "Lacakin adalah aplikasi sederhana untuk melacak kiriman paket dari berbagai ekspedisi di Indonesia.<br>"
            "Didukung ekspedisi populer seperti JNE, J&T, SiCepat, AnterAja, POS Indonesia, Shopee Express, dan lainnya.<br><br>"
            "© MUH. RESSA ARSY MA'RIF - F1D022137"
        )

        msg = QMessageBox(self)
        msg.setWindowTitle("Tentang")
        msg.setTextFormat(Qt.RichText)
        msg.setText(teks)
        msg.setStandardButtons(QMessageBox.Ok)

        if self.mode == "dark":
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #2c2c2c;
                    color: #f0f0f0;
                }
                QPushButton {
                    background-color: #3a3a3a;
                    color: #ffffff;
                    padding: 5px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #555;
                }
            """)

        msg.exec_()

    def _buat_statusbar(self):
        self.sb = QStatusBar()
        self.setStatusBar(self.sb)
        self.status_pesan = "MUH. RESSA ARSY MA'RIF - F1D022137"
        self.sb.showMessage(self.status_pesan)
        self.timer_status = QTimer()
        self.timer_status.timeout.connect(lambda: self.sb.showMessage(self.status_pesan))
        self.timer_status.start(3000)

    def _buat_database(self):
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS riwayat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no_resi TEXT,
                kurir TEXT,
                status TEXT,
                tgl_dicek TEXT,
                catatan TEXT
            )
        ''')
        con.commit()
        con.close()

    def _cek_resi(self):
        no_resi = self.in_resi.text().strip()
        nama_kurir = self.in_kurir.currentText()
        kurir = EKSPEDISI_MAP.get(nama_kurir)
        catatan = self.in_catatan.text().strip()

        if not no_resi:
            QMessageBox.warning(self, "Error", "Nomor resi tidak boleh kosong.")
            return

        try:
            res = requests.get(API_URL, params={
                "api_key": API_KEY,
                "courier": kurir,
                "awb": no_resi
            })
            data = res.json()
            if data["status"] == 200 and "data" in data:
                ringkasan = data["data"]["summary"]
                riwayat = data["data"]["history"]
                self._isi_tabel(riwayat)
                self._simpan_sqlite(no_resi, nama_kurir, ringkasan.get("status", "-"), catatan)
                QMessageBox.information(self, "Status", f"Status: {ringkasan.get('status', '-')}")
            else:
                QMessageBox.warning(self, "Gagal", data.get("message", "Resi tidak ditemukan atau kurir tidak valid."))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal koneksi ke API:\n{e}")

    def _isi_tabel(self, data):
        self.tabel.setRowCount(len(data))
        for i, item in enumerate(data):
            self.tabel.setItem(i, 0, QTableWidgetItem(item.get("date", "-")))
            self.tabel.setItem(i, 1, QTableWidgetItem(item.get("desc", "-")))

    def _simpan_sqlite(self, no_resi, kurir, status, catatan):
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute('''
            INSERT INTO riwayat (no_resi, kurir, status, tgl_dicek, catatan)
            VALUES (?, ?, ?, ?, ?)
        ''', (no_resi, kurir, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), catatan))
        con.commit()
        con.close()

    def _ekspor_pdf(self):
        if self.tabel.rowCount() == 0:
            QMessageBox.warning(self, "Kosong", "Belum ada data pelacakan untuk diekspor.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Simpan PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Laporan Pelacakan Resi - Lacakin", ln=True, align='C')
        pdf.set_font("Arial", "", 12)
        pdf.ln(10)

        resi = self.in_resi.text()
        kurir = self.in_kurir.currentText()
        catatan = self.in_catatan.text()
        tgl = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pdf.cell(0, 10, f"Nomor Resi : {resi}", ln=True)
        pdf.cell(0, 10, f"Kurir       : {kurir}", ln=True)
        pdf.cell(0, 10, f"Tanggal Cek : {tgl}", ln=True)
        if catatan:
            pdf.multi_cell(0, 10, f"Catatan     : {catatan}")
        pdf.ln(5)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(60, 10, "Tanggal", 1)
        pdf.cell(130, 10, "Keterangan", 1)
        pdf.ln()

        pdf.set_font("Arial", "", 11)
        for i in range(self.tabel.rowCount()):
            tanggal = self.tabel.item(i, 0).text()
            ket = self.tabel.item(i, 1).text()
            pdf.cell(60, 10, tanggal, 1)
            pdf.cell(130, 10, ket, 1)
            pdf.ln()

        pdf.output(path)
        QMessageBox.information(self, "Sukses", "Data berhasil diekspor ke PDF.")

    def _toggle_mode(self):
        if self.mode == "light":
            self._atur_style("dark")
            self.mode = "dark"
            self.btn_mode.setText("☀️")
        else:
            self._atur_style("light")
            self.mode = "light"
            self.btn_mode.setText("🌙")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CekResiFinal()
    win.show()
    sys.exit(app.exec_())