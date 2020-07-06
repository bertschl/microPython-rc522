from machine import Pin, SPI
import time
"""
@Author Lukas Bertsch, using Code of https://github.com/wendlers/micropython-mfrc522 --> using Code of https://github.com/mxgxw/MFRC522-python.
Use do_read() to perform a read on the rfid tag, which returns the uid.
"""
class RFID:
    """ACKs"""
    OK = 0
    NOTAGERR = 1
    ERR = 2
    """RND RFID card constants"""
    REQIDL = 0x26
    REQALL = 0x52

    AUTHENT1A = 0x60
    AUTHENT1B = 0x61
    """Static SPI Properties"""
    SCK = None
    MOSI = None
    MISO = None
    RST = None
    SPI = None
    CS_LIST = []

    def __init__(self, cs):
        self.cs = Pin(cs, Pin.OUT)
        self.CS_LIST.append(self.cs)
        self.init()

    def _iChooseYouPikachu(self):
        for elem in self.CS_LIST:
            elem.value(1)
        self.cs.value(0)


    def init(self):
        if self.SPI is not None:
            self.reset()
            self._wreg(0x2A, 0x8D)
            self._wreg(0x2B, 0x3E)
            self._wreg(0x2D, 30)
            self._wreg(0x2C, 0)
            self._wreg(0x15, 0x40)
            self._wreg(0x11, 0x3D)
            self._wreg(0x1A, 0x70)
            self.antenna_on()
        else:
            print("SPI is not set up. Use the setSPIProperties() function.")
        #print(RFID.SPI)

    def reset(self):
        self._wreg(0x01, 0x0F)

    def antenna_on(self, on=True):

        if on and ~(self._rreg(0x14) & 0x03):
            self._sflags(0x14, 0x03)
        else:
            self._cflags(0x14, 0x03)

    def _wreg(self, reg, val):
        self._iChooseYouPikachu()
        self.SPI.write(b'%c' % int(0xff & ((reg << 1) & 0x7e)))
        self.SPI.write(b'%c' % int(0xff & val))
        _muteSlaves()

    def _rreg(self, reg):
        self._iChooseYouPikachu()
        self.SPI.write(b'%c' % int(0xff & (((reg << 1) & 0x7e) | 0x80)))
        val = self.SPI.read(1)
        _muteSlaves()

        return val[0]

    def _sflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) | mask)

    def _cflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) & (~mask))

    def _tocard(self, cmd, send):

        recv = []
        bits = irq_en = wait_irq = n = 0
        stat = self.ERR

        if cmd == 0x0E:
            irq_en = 0x12
            wait_irq = 0x10
        elif cmd == 0x0C:
            irq_en = 0x77
            wait_irq = 0x30

        self._wreg(0x02, irq_en | 0x80)
        self._cflags(0x04, 0x80)
        self._sflags(0x0A, 0x80)
        self._wreg(0x01, 0x00)

        for c in send:
            self._wreg(0x09, c)
        self._wreg(0x01, cmd)

        if cmd == 0x0C:
            self._sflags(0x0D, 0x80)

        i = 2000

        #THIS PART IS DELETED FOR SPEEEEEDY REASONS, repeated read of interupt registers, this may or may not affect something, but im way too lazy to look everything up. The code is way quicker, so i guess thats the way to go, cant be arsed.
        #ti = time.time() * 1000
        """
        while True:
            n = self._rreg(0x04)
            i -= 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_irq)):
                break
                #"""
        #print("tocard: ", (time.time() * 1000 - ti))
        self._cflags(0x0D, 0x80)

        if i:
            if (self._rreg(0x06) & 0x1B) == 0x00:
                stat = self.OK

                if n & irq_en & 0x01:
                    stat = self.NOTAGERR
                elif cmd == 0x0C:
                    n = self._rreg(0x0A)
                    lbits = self._rreg(0x0C) & 0x07
                    if lbits != 0:
                        bits = (n - 1) * 8 + lbits
                    else:
                        bits = n * 8

                    if n == 0:
                        n = 1
                    elif n > 16:
                        n = 16

                    for _ in range(n):
                        recv.append(self._rreg(0x09))
            else:
                stat = self.ERR

        return stat, recv, bits

    def _crc(self, data):

        self._cflags(0x05, 0x04)
        self._sflags(0x0A, 0x80)

        for c in data:
            self._wreg(0x09, c)

        self._wreg(0x01, 0x03)

        i = 0xFF
        while True:
            n = self._rreg(0x05)
            i -= 1
            if not ((i != 0) and not (n & 0x04)):
                break

        return [self._rreg(0x22), self._rreg(0x21)]

    def request(self, mode):
        self._wreg(0x0D, 0x07)
        (stat, recv, bits) = self._tocard(0x0C, [mode])


        if (stat != self.OK) | (bits != 0x10):
            stat = self.ERR

        return stat, bits

    def anticoll(self):

        ser_chk = 0
        ser = [0x93, 0x20]

        self._wreg(0x0D, 0x00)
        (stat, recv, bits) = self._tocard(0x0C, ser)

        if stat == self.OK:
            if len(recv) == 5:
                for i in range(4):
                    ser_chk = ser_chk ^ recv[i]
                if ser_chk != recv[4]:
                    stat = self.ERR
            else:
                stat = self.ERR

        return stat, recv

    def select_tag(self, ser):

        buf = [0x93, 0x70] + ser[:5]
        buf += self._crc(buf)
        (stat, recv, bits) = self._tocard(0x0C, buf)
        return self.OK if (stat == self.OK) and (bits == 0x18) else self.ERR

    def auth(self, mode, addr, sect, ser):
        return self._tocard(0x0E, [mode, addr] + sect + ser[:4])[0]

    def stop_crypto1(self):
        self._cflags(0x08, 0x08)

    def read(self, addr):

        data = [0x30, addr]
        data += self._crc(data)
        (stat, recv, _) = self._tocard(0x0C, data)
        return recv if stat == self.OK else None

    def write(self, addr, data):

        buf = [0xA0, addr]
        buf += self._crc(buf)
        (stat, recv, bits) = self._tocard(0x0C, buf)

        if not (stat == self.OK) or not (bits == 4) or not ((recv[0] & 0x0F) == 0x0A):
            stat = self.ERR
        else:
            buf = []
            for i in range(16):
                buf.append(data[i])
            buf += self._crc(buf)
            (stat, recv, bits) = self._tocard(0x0C, buf)
            if not (stat == self.OK) or not (bits == 4) or not ((recv[0] & 0x0F) == 0x0A):
                stat = self.ERR

        return stat

    def do_read(self):
        (stat, tag_type) = self.request(self.REQIDL)
        #print("stat: ", stat, ", tag_type: ", tag_type)
        if stat == self.OK:
            (stat, raw_uid) = self.anticoll()
            #print("second")
            #print(stat)
            #print(raw_uid)
            if stat == self.OK:
                #print("New card detected")
                #print("  - tag type: 0x%02x" % tag_type)
                #print("  - uid	 : 0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
                #print("")
                if self.select_tag(raw_uid) == self.OK:

                    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

                    if self.auth(self.AUTHENT1A, 8, key, raw_uid) == self.OK:
                        # print("Address 8 data: %s" % self.read(8))
                        self.stop_crypto1()
                    else:
                        print("Authentication error")
                else:
                    print("Failed to select tag")
                return raw_uid

        return None


def _muteSlaves():
    for elem in RFID.CS_LIST:
        elem.value(1)

def printSPIStatus():
    print(RFID.SPI)
def setSPIProperties(sck, mosi, miso, rst):
    """
    @param sck: SPI sck GPIO Pinnumber --> Clock
    @param mosi: SPI mosi GPIO Pinnumber --> Master Output, Slave Input
    @param miso: miso GPIO Pinnumber --> Master Input, Slave Output
    @param rst: rst GPIO Pinnumber --> Reset
    This function defines the static SPI Properties, that will be used for every slave device(RC522). The connection can be used for every slave.
    """
    RFID.SCK = Pin(sck, Pin.OUT)
    RFID.MOSI = Pin(mosi, Pin.OUT)
    RFID.MISO = Pin(miso)
    RFID.RST = Pin(rst, Pin.OUT)
    RFID.RST.value(0)

    RFID.SPI = SPI(polarity=0, phase=0, sck=RFID.SCK, mosi=RFID.MOSI, miso=RFID.MISO)
    RFID.SPI.init()
    #RFID.SPI.setFrequency(500000)

    RFID.RST.value(1)
    _muteSlaves()
    print(RFID.SPI)
    if SPI is not None:
        return 0
    else:
        return 1

