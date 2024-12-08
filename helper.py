import struct
import zlib
import random

MAX_PACKET_NUMBER = 255

ACK = 0
SYN = 1
FIN = 2
MSG = 3
CHAOS = 0.5

def computeChecksum(seqNum, dataToSend=None):
    """Computes a checksum using the CRC32 algorithm after combining a sequence number and the payload
    
    Keyword arguments:
    seqNum -- sequence number (single byte)
    dataToSend -- data to be sent, default is None (empty payload)
    Returns: 32-bit checksum of the data
    """
    
    # empty payload to an empty byte string if it's None
    dataToSend = dataToSend or b''

    # convert the sequence number to a single byte, and concatenate with the payload
    data = struct.pack("B", seqNum) + dataToSend

    # compute the CRC32 checksum using zlib, and return it as a 32-bit value
    # use `& 0xFFFFFFFF` to make sure it's 32-bit unsigned value
    checksumVal = zlib.crc32(data)

    # simulate error 5% of the time by introducing random chance of error
    if random.random() < CHAOS:
        checksumVal = 0

    return (checksumVal & 0xFFFFFFFF)

def checkCorrupt(packet):
    """check to see if packets corrupted by using CRC32 algorithm
    
    Keyword arguments:
    packet
    Return: true if the packet is corrupted, false if it isn't
    """
    if len(packet) < 6: return True  # corrupted if it's too short

    seqNum = packet[1]  
    checksumReceived = int.from_bytes(packet[2:6], byteorder='big')  
    data = packet[6:]  

    # recompute checksum using sequence number and message
    computedChecksum = computeChecksum(seqNum, data)

    # compare received checksum with computed checksum
    return checksumReceived != computedChecksum

def createPacket(seqNum, packetType, msg=None):
    """creates ACK, SYN, FIN or MSG

    Keyword arguments:
    seqNum -- acknowledgement number (int)
    packetType -- ACK, SYN, or FIN (int)
    Return: ack
    """
    # combine packetType and ackNum into a packet with no data
    if packetType is not None:
        header = struct.pack('!B B', packetType, seqNum) #ackNum corresponds to packet number

    if msg is not None:
        # [1 byte packetType] + [1 byte seqNum] + [4 bytes for checksum] + [data]
        encodedMsg = msg.encode()
        checksum = computeChecksum(seqNum, encodedMsg)
        packet = header + checksum.to_bytes(4, byteorder='big') + encodedMsg
    else:
        # [1 byte packetType] + [1 byte seqNum] + [4 bytes for checksum]
        checksum = computeChecksum(seqNum, dataToSend=None)
        packet = header + checksum.to_bytes(4, byteorder='big')
    
    return packet

def parsePacket(packet):
    """extracts the packet type, sequence number, and data from packet
    
    Keyword arguments:
    packet -- (byte string)

    Returns:
    packetType -- type of the packet (data, ACK, FIN)
    seqNum -- sequence number of the packet
    data -- actual data payload of the packet
    """ 
    # [1 byte packetType] + [1 byte seqNum] + [4 bytes for checksum] + [data]

    packetType, seqNum, checksum = struct.unpack('!B B I', packet[:6])
    data = packet[6:]
    return packetType, seqNum, data

def handshakePacket():
    return createPacket(0, SYN)

def endPacket():
    return createPacket(0, FIN)

def ackPacket(seqNum):
    return createPacket(seqNum, ACK)

def isSYN(packet):
    packetType, seqNum, data = parsePacket(packet)
    if (packetType != SYN):
        return False
    return True

def getPacketNumber(packet):
    packetType, seqNum, data = parsePacket(packet)
    return seqNum
    
def isAck(packet):
    packetType, seqNum, data = parsePacket(packet)
    return packetType == ACK

def isEnd(packet):
    packetType, seqNum, data = parsePacket(packet)
    return packetType == FIN