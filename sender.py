import sys
import socket
import threading
import time
from helper import * # get's everything directly

#GLOBAL_VARS
CONTROL_TIMEOUT = 10
ACK_TIMEOUT = 1
END_TIMEOUT = 10
SOCK_TIMEOUT = 10

TOTAL_PACKETS = 10 #Size of arr in sliding window
MAX_UNACKED = 4 #Congestion control

#ports
HOST_NAME = 'localhost'
HOST_PORT = 1024
destName = 'localhost'
destPort = 8080

hostSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
hostSock.bind((HOST_NAME, HOST_PORT))
# hostSock.timeout(SOCK_TIMEOUT)
destSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #is unbound so it uses any port to send

#congestion control
congestion = 0 #unAcked packages
congestionLock = threading.Lock()

#window
packets = [0 for _ in range(TOTAL_PACKETS * 2)]
start = 0
flowControl = TOTAL_PACKETS // 2 #window end, integer division
current = start

#packet
packetNumber = 0

#others
endConfirmed = False

def send(message, packetNumber):
    global congestion
    with congestionLock:
        congestion = congestion + 1
    
    while (not packets[packetNumber % TOTAL_PACKETS]):
        if (endConfirmed): #ENDING
            return
        destSock.sendto(createPacket(packetNumber, MSG, message), (destName, destPort))
        time.sleep(ACK_TIMEOUT)

    # print(f"Got ACK for {packetNumber}") # FOR DEBUG
    with congestionLock:
        congestion = congestion - 1

def incrementWindow():
    global flowControl, start
    flowControl = (flowControl + 1) % TOTAL_PACKETS
    packets[flowControl] = 0
    start = (start + 1) % TOTAL_PACKETS

# ASSUME: when ending, wait for all packets to finish sending
def ackMaster():
    global endConfirmed
    while (True):
        data, addr = hostSock.recvfrom(1024) #1024 is the buffer size, not the port
        if (isAck(data)):
            packetNumber = getPacketNumber(data)
            index = packetNumber % TOTAL_PACKETS
            packets[index] = 1 # set to ACKED
            if (index == start):
                incrementWindow()
        if (isEnd(data)):
            endConfirmed = True
            return

#for flow control, returns true if trying to send past window
def overflow():
    if (current + 1 >= flowControl):
        print("Controlling flow")
        return True
    return False

#for congestion control, returns true if too many unacked packets
def congested():
    if (congestion + 1 > MAX_UNACKED):
        print("Controlling congestion")
        return True
    return False

handshaked = False
# ASSUME: user gives valid destName and destPort
def handshake():
    # global destName, destPort
    # destName = sys.argv[1]
    # destPort = int(sys.argv[2])

    threading.Thread(target=handshakeConfirm).start()

    while (not handshaked):
        print('Sending handshake')
        destSock.sendto(handshakePacket(), (destName, destPort))
        time.sleep(ACK_TIMEOUT)

def handshakeConfirm():
    global handshaked
    while (True):
        packet, addr = hostSock.recvfrom(1024) # TO DO: need to make sure that the address received is the same as the one sent
        if (isSYN(packet)):
            handshaked = True
            print('Handshaked confirmed')
            return
        print('not a handshake')

def endConnection():
    while (not endConfirmed):
        time.sleep(ACK_TIMEOUT)
        destSock.sendto(endPacket(), (destName, destPort))
    print("Shutting down...")
    time.sleep(END_TIMEOUT)

def main():
    global packetNumber, current
    # if (len(sys.argv) <= 1):
    #     print("Bad args, ending program...")
    #     return

    handshake()
    threading.Thread(target=ackMaster).start()

    while (True):
        if (congested() or overflow()):
            time.sleep(CONTROL_TIMEOUT)
        # else -> 
        current = current + 1
        
        message = input('Enter message (or \"quit\" to exit): ')
        if (message == 'quit'):
            endConnection()
            break
        threading.Thread(target=send, args=(message, packetNumber)).start()

        packetNumber = (packetNumber + 1) % MAX_PACKET_NUMBER

    hostSock.close()
    destSock.close()
    print("Sender closed.")

main()
