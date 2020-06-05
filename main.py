import socket
import sys
import time

import mido
import mido.backends.rtmidi
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap

from udp_accelgyro import UdpAg, UdpAgPhone

sys.path.append('/Users/robbin/PycharmProjects/midi2/BreezeStyleSheets-master')

import breeze_resources


class FirstMidiWindow(QMainWindow):
    def __init__(self):
        super(FirstMidiWindow, self).__init__()
        self.setGeometry(300, 200, 580, 300)
        self.setFixedSize(580, 300)
        self.setWindowTitle('MIDIator')
        self.initUI()
        self.worker = UdpAg()
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

    def initUI(self):
        self.label = QtWidgets.QLabel(self)
        self.label.setText("Select midi device:")
        self.label.setGeometry(50, 20, 130, 20)
        # self.label.move(20, 30)

        self.comboBox = QtWidgets.QComboBox(self)
        self.comboBox.setGeometry(30, 40, 161, 32)
        self.comboBox.addItems(["Micropython Accelerometer", "Sensor_Data iOS app Accelerometer"])

        self.label = QtWidgets.QLabel(self)
        self.label.setText("Select midi output:")
        self.label.setGeometry(50, 220, 130, 20)

        self.comboBox2 = QtWidgets.QComboBox(self)
        self.comboBox2.setGeometry(30, 240, 161, 32)
        # to populate box find available midi devices
        midi_devs = self.find_midi_out()
        self.comboBox2.addItems(midi_devs)

        self.label2 = QtWidgets.QLabel(self)
        self.label2.setText("Set local ip address:")
        self.label2.setGeometry(50, 90, 140, 20)

        self.lineEdit = QtWidgets.QLineEdit(self)
        self.lineEdit.setGeometry(30, 110, 161, 21)
        self.lineEdit.setAlignment(QtCore.Qt.AlignCenter)

        self.dial = QtWidgets.QDial(self)
        self.dial.setGeometry(270, 73, 50, 50)
        self.dial.setMinimum(0)
        self.dial.setMaximum(127)
        self.dial.setValue(64)
        # self.label3 = QtWidgets.QLabel(self)
        # self.label3.setText("midi send data:")
        # self.label3.setGeometry(230, 70, 161, 21)

        self.label4 = QtWidgets.QLabel(self)
        self.label4.setText("")
        self.label4.setGeometry(230, 140, 161, 21)

        self.b1 = QtWidgets.QPushButton(self)
        self.b1.setGeometry(50, 140, 112, 32)
        self.b1.setText("Find ip")
        self.b1.clicked.connect(self.find_ip)

        self.label2 = QtWidgets.QLabel(self)
        self.label2.setText("Default port: 5045")
        self.label2.setGeometry(50, 180, 140, 20)

        self.b2 = QtWidgets.QPushButton(self)
        self.b2.setGeometry(220, 40, 150, 30)
        self.b2.setText("Start MIDI")
        self.b2.clicked.connect(self.open_udp)

        self.b3 = QtWidgets.QPushButton(self)
        self.b3.setGeometry(220, 130, 150, 30)
        self.b3.setText("Stop MIDI")
        self.b3.clicked.connect(lambda x=False: self.worker.stoprunning(x))
        self.b3.setEnabled(False)

        # control buttons for different midi sliders
        self.c1 = QtWidgets.QCheckBox(self)
        self.c1.setGeometry(210, 170, 90, 30)
        self.c1.setText("control A")
        # self.c1.setChecked(True)
        self.c1.setDisabled(True)
        self.c1.pressed.connect(lambda: self.gui_checkboxes_changed(self.c1))

        self.c2 = QtWidgets.QCheckBox(self)
        self.c2.setGeometry(300, 170, 90, 30)
        self.c2.setText("control B")
        self.c2.setDisabled(True)
        self.c2.pressed.connect(lambda: self.gui_checkboxes_changed(self.c2))

        self.c3 = QtWidgets.QCheckBox(self)
        self.c3.setGeometry(210, 200, 90, 30)
        self.c3.setText("control C")
        self.c3.setDisabled(True)
        self.c3.pressed.connect(lambda: self.gui_checkboxes_changed(self.c3))

        self.c4 = QtWidgets.QCheckBox(self)
        self.c4.setGeometry(300, 200, 90, 30)
        self.c4.setText("control D")
        self.c4.setDisabled(True)
        self.c4.pressed.connect(lambda: self.gui_checkboxes_changed(self.c4))

        # make a list of the checkboxes for easy acces
        self.cboxlist = [self.c1, self.c2, self.c3, self.c4]

        # create a dictionary for channels per control
        self.cboxchannlist = {}
        for i, box in enumerate(self.cboxlist):
            self.cboxchannlist[box.text()] = i + 1

        # self.label.setFocus()

        # self.setWindowIcon(QtGui.QIcon('piano.ico'))

        # image en opmaak

        self.labelimage = QtWidgets.QLabel(self)
        self.labelimage.setGeometry(400, 60, 190, 270)
        pixmap = QPixmap("Midiatoricon.png")
        self.labelimage.setPixmap(pixmap)

        self.labelapp = QtWidgets.QLabel(self)
        self.labelapp.setText("MIDIator")
        self.labelapp.setGeometry(425, 2, 160, 50)
        self.labelapp.setStyleSheet("""
                QWidget {
                    /*border: 1px solid black;
                    border-radius: 10px;*/
                    color: #bdbdbd;
                    font-size: 40px;
                    }
                """)

    def find_ip(self):
        ipsearch = socket.gethostbyname_ex(socket.gethostname())[-1]
        if len(ipsearch) == 1:
            self.lineEdit.setText(ipsearch[0])
        elif len(ipsearch) > 1:
            self.lineEdit.setText(ipsearch[1])
        else:
            self.lineEdit.setText("no autofind")
        self.lineEdit.repaint()
        # QApplication.processEvents()
        # QApplication.focusWidget().clearFocus()

    def open_udp(self):
        # first check if everything is set-up correctly if not throw error
        print(self.lineEdit.text())
        if self.lineEdit.text() == "":
            print("joehoe")
            self.show_popup("Insert the local ip address in the corresponding textbox")
            return
        # if this works than try to bind a socket to listen to this ip address
        self.udpip = self.lineEdit.text()
        self.port = 5045
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1)
        try:
            self.sock.bind((self.udpip, self.port))
        except:
            self.show_popup("couldn't bind socket to ip. Check ip and check if port 5045 is available (firewall settings)")
            return
        # do the midi stuff here
        # where to write the midi to;
        try:
            self.outport = mido.open_output(self.comboBox2.currentText())
        except:
            self.show_popup("couldn't open midi device")
            return
        # if everything works out enter the loop to search for udp inputs
        # the proper function is selected based on combobox
        if self.comboBox.currentIndex() == 0:
            # QApplication.processEvents()
            self.udp_micro_accel()
            time.sleep(0.02)
            self.guibuttonupdatestart()
        elif self.comboBox.currentIndex() == 1:
            # QApplication.processEvents()
            self.udp_phone_accel()
            time.sleep(0.02)
            self.guibuttonupdatestart()

    def show_popup(self, msg):
        popup = QMessageBox()
        popup.setWindowTitle("midicontroller")
        popup.setText(msg)

        x = popup.exec_()

    def find_midi_out(self):
        ports_avail = mido.get_input_names()
        return ports_avail

    def update(self):
        self.label.adjustSize()

    def udp_micro_accel(self):
        self.worker = UdpAg(self.port, self.udpip, self.sock, self.outport)
        self.threadpool.start(self.worker)
        self.worker.signal.new_signal.connect(self.close_sock)

    def udp_phone_accel(self):
        self.worker = UdpAgPhone(self.port, self.udpip, self.sock, self.outport)
        self.threadpool.start(self.worker)
        self.worker.signal.new_signal.connect(self.close_sock)
        self.worker.signal.data_signal.connect(self.updategui)

    @pyqtSlot(int)
    def close_sock(self, sig):
        self.sock.close()
        print(sig)
        self.guibuttonupdatestop()
        # QApplication.processEvents()

    @pyqtSlot(int)
    def updategui(self, controlnew):
        # update the gui from the received midi control data
        self.dial.setValue(controlnew)
        self.dial.repaint()

    @pyqtSlot(int)
    def channelchangegui(self, channel):
        # handle change of midi channels
        pass

    def guibuttonupdatestart(self):
        # change button states when pressing start
        self.b3.setDisabled(False)
        self.c1.setDisabled(False)
        self.c2.setDisabled(False)
        self.c3.setDisabled(False)
        self.c4.setDisabled(False)
        self.b2.setEnabled(False)
        self.b2.repaint()
        self.b3.repaint()
        self.c1.repaint()
        self.c2.repaint()
        self.c3.repaint()
        self.c4.repaint()
        # check if a button is still checked and if so disable it and use this channel as the midi channel
        # so sent it to the worker thread
        for box in self.cboxlist:
            if box.isChecked():
                self.worker.change_channel(self.cboxchannlist[box.text()])
                box.setDisabled(True)
                box.repaint()

    def guibuttonupdatestop(self):
        # change button states when stop
        self.b3.setEnabled(False)
        self.b2.setDisabled(False)
        self.c1.setEnabled(False)
        self.c2.setEnabled(False)
        self.c3.setEnabled(False)
        self.c4.setEnabled(False)
        self.b2.repaint()
        self.b3.repaint()
        self.c1.repaint()
        self.c2.repaint()
        self.c3.repaint()
        self.c4.repaint()

    def gui_checkboxes_changed(self, cbox):
        # check whats happening to the checkboxes and update accordingly

        # uncheck and enable all boxes
        for box in self.cboxlist:
            box.setChecked(False)
            box.setEnabled(True)

        # check the current box and disable it
        cbox.setChecked(True)
        cbox.setDisabled(True)

        # then send a signal to the worker to use this channel
        self.worker.change_channel(self.cboxchannlist[cbox.text()])

        for box in self.cboxlist:
            box.repaint()

def window():
    app = QApplication(sys.argv)

    # set stylesheet
    file = QFile(":/dark.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    app.setStyleSheet(stream.readAll())

    # app.setStyle('QtCurve')

    win = FirstMidiWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    window()