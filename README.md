# MIDIator

A simple Python application to receive data over a UDP socket and translate it into MIDI control changes.
The GUI is written in PyQt5.

## Usage:

### Running main.py directly using Python 3

To run the main script directly:

> 1. Clone or download this git repository to your local machine and cd into the main folder
> 2. Create and activate a virtual environment with Python 3.8.2 (earlier Python3 releases might also be ok)
> 3. Install dependencies into the virtual environment using *pip install -r requirements.txt*
> 4. cd into the main folder (the folder with all *.py* files) before running any scripts/functions.

### Running the prebuild version

Soon, executables will be available for download directly from here for Linux, Windows and Mac platforms. These require no installation whatsoever.

## Micropython

For Micropython some scripts are given to get started on the UDP connection and a sample code reads raw data from the MPU-6050 to send accelerometer and gyroscope data from the microcontroller to the UDP socket. 


#### Add custom midi-device:

> The program is written in such a way that it should be easy to customize the interface (i.e. add more controls or other midi events). Currently the devices (iphone orientation and micropython) are represented by a QRunnable class in "udp_accelgyro.py". Other classes can be added here and then also in the main.py they should be added to the combobox in line 38:

```python
self.comboBox.addItems(["Micropython Accelerometer", "Sensor_Data iOS app Accelerometer"])
```

> and then on line 200 is where based on the combobox selection a function (line 226, 231) is run to start an instance of any of the available classes in "udp_accelgyro.py":

```python
if self.comboBox.currentIndex() == 0:
            # QApplication.processEvents()
            self.udp_micro_accel()
            time.sleep(0.02)
            self.guibuttonupdatestart()

...

def udp_micro_accel(self):
        self.worker = UdpAg(self.port, self.udpip, self.sock, self.outport)
        self.threadpool.start(self.worker)
        self.worker.signal.new_signal.connect(self.close_sock)
```

> It is importent to work with QRunnable classes and start the "workers" using QThreadpool(). Since receiving on the UDP socket is done using socket.recvfrom() and this is a blocking call. Running it in the same thread as the main application would freeze the GUI and the app would go unresponsive.

### Current implementation includes:

* using the orientation sensor of your phone (using sensor data streamer on iOS)
* using a microcontroller running micropython and the given source code (also using orientation to control MIDI sliders)

## Acknowledgements

The dark breeze theme is directly copied from Alexhuszagh his [BreezeStyleSheets](https://github.com/Alexhuszagh/BreezeStyleSheets "BreezeStyleSheets") which is based on [QDarkStylesheet](https://github.com/ColinDuquesnoy/QDarkStyleSheet "QDarkStylesheet")

For micropython and the MPU6050 inertial sensor the [I2C library](https://github.com/adamjezek98/MPU6050-ESP8266-MicroPython "i2c") by adamjezek98 was used and is included
