import socket
from helper import *

expectedSeq = 0 # next expected sequence number
ht = {} # ht to store out of order packets

#ports
HOST_NAME = 'localhost'
HOST_PORT = 8080 # so not to conflict on local computer?
destName = 'localhost' # get's it in handshake
destPort = 1024

hostSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
hostSock.bind((HOST_NAME, HOST_PORT))
destSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #is unbound so it uses any port to send

# TO DO:
def awaitHandshake():
    while (True):
        packet, addr = hostSock.recvfrom(1024)
        if (isSYN(packet)):
            destSock.sendto(handshakePacket(), (destName, destPort)) #TO DO: make dynamic
            print("Handshook, sending back")
            return addr

def main():
    global expectedSeq
    senderAddr = awaitHandshake()
    while True:
        packet, addr = hostSock.recvfrom(1024)

        # make sure it is the right sender
        # if (addr != senderAddr):
        #     continue

        if checkCorrupt(packet) == True:
            print("Got corrupted packet") # FOR DEBUG
            continue
        
        packetType, seqNum, data = parsePacket(packet)
        destSock.sendto(ackPacket(seqNum), (destName, destPort))
        if (packetType == MSG):
            if (seqNum == expectedSeq):
                msg = data.decode()
                print(f"recieved: {msg}")
                expectedSeq = (expectedSeq + 1) % MAX_PACKET_NUMBER

                while expectedSeq in ht:
                    nextData = ht.pop(expectedSeq)
                    nextMsg = nextData.decode()
                    print(f"received from buf: {nextMsg}")
                    expectedSeq = (expectedSeq + 1) % MAX_PACKET_NUMBER
            else:
                # print(f"received packet out of order: {seqNum}") # FOR DEBUG
                ht[seqNum] = data
        elif (packetType == FIN):
            destSock.sendto(endPacket(), (destName, destPort))
            break

    hostSock.close()
    destSock.close()
    print("Receiver closed.")
main()
