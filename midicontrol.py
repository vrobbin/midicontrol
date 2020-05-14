import socket
import ast
import mido


def midicontwheel(min, max, lower, upper, midiport):
    # first set-up udp socket for listening to udp packets
    udpip = "192.168.0.103"
    port = 80

    sock = socket.socket(socket.AF_INET,  # Internet
                         socket.SOCK_DGRAM)  # UDP
    sock.bind((udpip, port))

    # set-up midi control
    outport = mido.open_output(midiport)

    # then infinite loop keeping track of amount of loop passes
    num = 0
    controlold = 0
    while True:
        # listen to data received over UDP
        data, addr = sock.recvfrom(128)  # buffer size is 1024 bytes
        # decode and store in dictionary
        dat = (ast.literal_eval(str(data.decode('ASCII'))))
        control = int(dat['AcZ'])
        # map acceleration AcX to control wheel using lower and upper bounds
        # it should be noted UDP AcX is between -14000 and +14000
        controlnew = round(mapper(control, max, min, lower, upper))
        # check if bounds are correct:
        if controlnew > 127:
            controlnew = 127
        elif controlnew < 0:
            controlnew = 0
        if controlnew != controlold:
            # send midi control change message
            outport.send(mido.Message('control_change', channel=1, control=controlnew))
            controlold = controlnew


def mapper(control, max, min, lower, upper):
    # first find new control mapped in the right range
    contmult = (max - min) / (upper - lower)
    newcont = control * contmult
    # determine proper shifting
    controlnew = newcont - min + lower
    # return newcontrolval
    return controlnew
