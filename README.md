# Interface Class for MicroPython and RC522 for multiple slaves

## Description

**NOTE: This Project is not actively updated**   
This Project uses [wendlers' Interface class](https://github.com/wendlers/micropython-mfrc522), which uses [this Raspberry PI Project](https://github.com/mxgxw/MFRC522-python) as a template.
The purpose of this project is to interfer with two or more rc522 RFID-Reader (slaves) and a ESP8266 Microcontroller as master.
However the template was not capable (at least in this exact scenario) of using multiple slaves, so i changed the SPI handling and the interface methods.
Note: This project uses a **Independent slave configuration**.

## Usage

1. Use *RFID.setSPIProperties(sck, mosi, miso, rst)*, which is a static method, to configure the shared SPI configuration for every slave. The paramters are **pin numbers**, **not** *Pin(xy, PIN.OUT)*.
2. Use the constructor *RFID.RFID(cs)* to get an object with the given cs/ss pin.
3. *object.do_read()* to check if a RFID chip is present, returns the raw uid if yes otherwhise *None*.   
**The method/class manages ALL SPI handling, so only these 3 methods have to be used.**
