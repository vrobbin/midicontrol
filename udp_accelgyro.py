from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import socket
import time
import ast
import mido
import rtmidi
from scipy import signal
import numpy as np
import math

class WorkerSignals(QObject):
    new_signal = pyqtSignal(int)
    data_signal = pyqtSignal(int)
    channel_signal = pyqtSignal(int)


class UdpAg(QRunnable):
    '''
    Worker thread
    '''

    def __init__(self, port=None, udpip=None, sock=None, outport=None):
        super(UdpAg, self).__init__()
        self.port = port
        self.udpip = udpip
        self.sock = sock
        self.outport = outport
        self.signal = WorkerSignals()

        # the channel can be changed to control 4 different sliders simultaneously (channels 1,2,3,4 are used)
        self.channel = 1

    @pyqtSlot()
    def stoprunning(self, runs):
        self.running = runs
        print("stopped")
        sig = 2
        self.signal.new_signal.emit(sig)

    @pyqtSlot()
    def change_channel(self, chann):
        self.channel = chann
        print("channel changed")
        self.signal.channel_signal.emit(chann)


    def mapper(self, control, max, min, lower, upper):
        # first find new control mapped in the right range
        contmult = (upper - lower) / (max - min)
        newcont = control * contmult
        # print(newcont)
        # determine proper shifting
        controlnew = newcont + ((upper - lower) / 2)
        # print(controlnew)
        # return newcontrolval
        return controlnew

    @pyqtSlot()
    def run(self):
        # infinite loop keeping track of amount of loop passes
        controlold = 0
        self.running = True
        while self.running:
            # listen to data received over UDP
            try:
                data, addr = self.sock.recvfrom(128)  # buffer size is 1024 bytes
            except:
                print("timeout no data received")
                continue
            # decode and store in dictionary
            dat = (ast.literal_eval(str(data.decode('ASCII'))))
            control = int(dat['AcX'])
            # map acceleration AcX to control wheel using lower and upper bounds
            # it should be noted UDP AcX is between -14000 and +14000
            controlnew = round(self.mapper(control, 14500, -14500, 0, 127))
            # print(controlnew)
            # check if bounds are correct:
            if controlnew > 127:
                controlnew = 127
            elif controlnew < 0:
                controlnew = 0
            if controlnew != controlold:
                # send midi control change message
                self.outport.send(mido.Message('control_change', channel=channel, value=controlnew))
                # print(controlnew)
                controlold = controlnew
                print(controlnew)

        # else:
        #     self.sock.close()
        #     sig = 2
        #     self.signal.new_signal.emit(sig)

class UdpAgPhone(QRunnable):
    '''
    Worker thread
    '''

    def __init__(self, port=None, udpip=None, sock=None, outport=None):
        super(UdpAgPhone, self).__init__()
        self.port = port
        self.udpip = udpip
        self.sock = sock
        self.outport = outport
        self.signal = WorkerSignals()

        # channels
        self.channel = 1

        # filter init
        self.b = signal.firwin(7, 0.01)
        self.z = signal.lfilter_zi(self.b, 1)
        self.result = [1]

        # smooth init
        self.current_angle = 0
        self.time = 0
        self.gyrangle = 0

    @pyqtSlot()
    def stoprunning(self, runs):
        self.running = runs
        print("stopped")
        sig = 2
        self.signal.new_signal.emit(sig)

    @pyqtSlot()
    def change_channel(self, chann):
        self.channel = chann
        print(f"channel changed to {self.channel}")

    def mapper(self, control, max, min, lower, upper):
        # first find new control mapped in the right range
        contmult = (upper - lower) / (max - min)
        newcont = control * contmult
        # print(newcont)
        # determine proper shifting
        controlnew = newcont + ((upper - lower) / 2)
        if controlnew < lower:
            controlnew = lower
            return lower
        elif controlnew > upper:
            controlnew = upper
            return upper
        # print(controlnew)
        # return newcontrolval
        return int(controlnew[0])

    def midi_smooth(self, newaccx, newaccy, newaccz, newgyro, dt):
        # acceleration value between -1 and 1 mapped to angle -90 to 90 deg
        if newaccz < 0:
            self.accangle = np.rad2deg(math.atan2(newaccx, math.sqrt(newaccy*newaccy + newaccz*newaccz)))
        else:
            self.accangle = np.rad2deg(math.atan2(newaccx, -math.sqrt(newaccy * newaccy + newaccz * newaccz)))
        # if newaccz > 0 and self.accangle < 0:
        #     self.accangle = -180 + self.accangle
        # if newaccz > 0 and self.accangle > 0:
        #     self.accangle = 180 - self.accangle
        # print(newaccx, newaccy, newaccz)
        # gyroscope value assume rad/s for now
        gyr = np.rad2deg(newgyro)
        self.current_angle = 0.05 * self.accangle + 0.95 * (self.current_angle + (gyr * dt))
        self.time = self.time + dt
        self.gyrangle = self.gyrangle + (gyr * dt)

    def filter_sbs(self):
        self.result.append(signal.lfilter(self.b, 1, [self.current_angle], zi=self.z)[0])
        self.z = signal.lfilter(self.b, 1, [self.current_angle], zi=self.z)[1]
        return True

    @pyqtSlot()
    def run(self):
        # infinite loop keeping track of amount of loop passes
        controlold = 0
        self.running = True
        while self.running:
            # listen to data received over UDP
            try:
                data, addr = self.sock.recvfrom(128)  # buffer size is 1024 bytes
            except:
                print("timeout no data received")
                continue
            # decode and store in dictionary
            accx = float(data.decode("ASCII").split(";")[6].split(":")[1])
            accy = float(data.decode("ASCII").split(";")[7].split(":")[1])
            accz = float(data.decode("ASCII").split(";")[8].split(":")[1])
            gyr = float(data.decode("ASCII").split(";")[3].split(":")[1])
            # control = int(dat['AcX'])
            self.midi_smooth(accx, accy, accz, gyr, 0.05)
            self.filter_sbs()
            controlnew = self.mapper(self.result[-1], 90, -90, 0, 127)
            if controlnew != controlold:
                # send midi control change message
                self.outport.send(mido.Message('control_change', channel=self.channel, value=controlnew))
                # also send to the GUI
                self.signal.data_signal.emit(controlnew)
                # print(controlnew)
                controlold = controlnew
                print(controlnew)
                print(self.channel)