import sys
sys.path.append("./")

import serial
import RTRQ.NodeEvent.NodeVideo as NodeText
import asyncio

class obj_Serial:
    def __init__(self, port, baudrate) -> None:
        self.root = serial.Serial()     
        self.port = port
        self.baudrate = baudrate
        NodeText.Video1.add_callback(self.write_data)

    def open(self):
        if self.root.is_open:
            self.root.close()
        self.root.timeout = 0
        self.root.port = self.port
        self.root.baudrate = self.baudrate
        self.root.open()

    def close(self):
        if self.root.is_open:
            self.root.close()

    def write_data(self, new_value):
        try:
            data = str(new_value).encode()
            self.root.write(data)
        except Exception as e:
            print(f"Error writing data: {e}")

    def read_data(self):
        try:
            if self.root.in_waiting > 0:
                NodeText.Video2.value = self.root.readline().decode().strip()
        except:
            None

    async def serial_runtime(self):
        while 1: 
            self.read_data()
            await asyncio.sleep(0.00001)

    def run(self):
        self.open()
        asyncio.run(self.serial_runtime())

def run_Serial():
    hello = obj_Serial('COM7', 115200)
    hello.run()