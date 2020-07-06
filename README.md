Interface Class for MicroPython and RC522 for multiple slaves
===============================
This Project uses [wendlers' Interface class](https://github.com/wendlers/micropython-mfrc522), which uses [this Raspberry PI Project](https://github.com/mxgxw/MFRC522-python) as a template.
The purpose of this project is to interfer with two or more rc522 RFID-Reader (slaves) and a ESP8266 Microcontroller as master.
However the template was not capable (at least in this exact scenario) of using multiple slaves, so i changed the SPI handling and the interface methods.
Note: This project uses 
===============================
Usage
===============================
1. Use "def setSPIProperties(sck, mosi, miso, rst)" to configure the shared SPI configuration for every slave.