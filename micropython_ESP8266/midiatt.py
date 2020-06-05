from machine import I2C, Pin
from time import sleep
import mpu6050
import network
import socket


def midisend():
	wlan = network.WLAN(network.STA_IF)
	sleep(0.5)
	wlan.active(True)
	while not wlan.isconnected():
		print("not connected yet")

	# set up socket
	udpip = "192.168.0.106"
	port = 5045
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	i2c = I2C(scl=Pin(5), sda=Pin(4))
	mpu = mpu6050.accel(i2c)

	# infinite loop of sending data
	while True:
		sleep(0.05)
		dat = mpu.get_values()
		barr = bytes(str(dat), 'utf-8')
		sock.sendto(barr, (udpip, port))

