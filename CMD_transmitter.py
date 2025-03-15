import dataclasses
import time
import re
import serial
import serial.tools.list_ports
import sys
import json

try:
    with open(".\\setting.json") as json_file:
        setting = json.load(json_file)["CMD_transmitter"]
except FileNotFoundError as e:
    print(e)
    print("Apply default settings")
    setting = {
        "retransmit_time": 0, 
        "timeout": 2.0, 
        "is_add_SFD": False, 
        "is_add_CRC": False 
    }

 
# for print message decoration
class Print:
    RED     = '\033[31m'
    YELLOW  = '\033[33m'
    BLUE    = '\033[34m'
    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    ERROR   = f'{RED}[ERROR]{RESET}'
    INFO    = f'{BLUE}[INFO] {RESET}'
    EVENT   = f'{YELLOW}[EVENT]{RESET}'
    LINE    = '=' * 30

    @staticmethod
    def space_every_two_str(bytes: bytes) -> str:
        return " ".join(bytes.hex()[i:i+2].upper() for i in range(0, len(bytes.hex()), 2))
    
    def transmit(frame: bytes) -> None:
        print(f'\n{Print.EVENT} PC > > > {Print.BOLD}[{Print.space_every_two_str(frame)}]{Print.RESET}\n')

    def receive(frame: bytes) -> None:
        print(f'\n{Print.EVENT} PC < < < {Print.BOLD}[{Print.space_every_two_str(frame)}]{Print.RESET}\n')

@dataclasses.dataclass
class FrameData:
    frame_id: bytes
    payload: bytes | None


# command making, check etc...
class Command:
    # most foundamental define
    SFD = b'\xAA'

    # # flame id (mis mcu receive)
    # STATUS_CHECK = b'\x01'
    # IS_SMF_AVAILABLE = b'\x02'

    # # IS_SMF_AVAILABLE payload
    # ALLOW = b'\x00'
    # DENY = b'\x01'

    # # flame id (boss pic receive)
    # MIS_MCU_STATUS = b'\x01'

    # # MIS_MCU_STATUS payload
    # EXECTING_MISSION = b'\x00'
    # REQ_COPY_TO_SMF = b'\x01'
    # COPYING_TO_SMF = b'\x02'
    # FINISHED_MISSION = b'\x03'

    # # flame id (common)
    # UL_CMD = b'\x00'
    # ACK = b'\x0F'


    is_add_SFD = setting["is_add_SFD"]
    is_add_CRC = setting["is_add_CRC"]

    Devices = {0x00: 'GS', 0x01: 'MAIN PIC', 0x02: 'COM PIC', 0x03: 'RESET PIC', 0x04: 'FAB PIC', 0x05: 'BOSS PIC', 
                       0x06: 'APRS PIC', 0x07: 'CAM MCU', 0x08: 'CHO MCU', 
                       0x09: 'SATO PIC', 0x0A: 'NAKA PIC', 0x0B: 'BHU MCU'}
    Frame_Id = {0x00: 'Uplink Command', 0x01: 'Status Check', 0x02: 'is SMF available'}

    def __init__(self):
        self.device_id = None
        # self.frame_id = Command.UL_CMD

    def select_device(self):
        print('\nSelect your device:')
        for id, name in Command.Devices.items():
            print(f'{id:X}) {name}   ', end='\t')
            if id % 5 == 4:
                print()
        print()
        while True:
            choice = input('> ').strip().upper()
            if re.fullmatch(f'^[0-9A-F]$', choice):
                self.device_id = bytes.fromhex('0' + choice)
                print(f'Use device: {Print.BOLD}{Command.Devices[int(choice, 16)]}{Print.RESET}')
                return

    def input_payload(self, com: serial.Serial) -> bytes:
        print('  __ __ __ __ __ __ __ __ __')
        while True:
            input_str = input('> ').replace(' ', '').upper()
            if re.fullmatch("^[0-9A-F]+$", input_str):
                if len(input_str) % 2 == 0:
                    return bytes.fromhex(input_str)
            elif re.fullmatch("^EXIT$", input_str):
                close_and_exit(com)

    def make_frame(self, payload: bytes) -> bytes:
        # header = ((self.device_id[0] << 4) | self.frame_id[0]).to_bytes(1, 'big')
        # crc = Command.calc_crc(header + payload)
        # return Command.SFD + header + payload + crc
        return (Command.SFD if Command.is_add_SFD else b'') + payload + (Command.calc_crc(payload) if Command.is_add_CRC else b'')

            
    @staticmethod
    def check_SFD(frame: bytes) -> bytes | None:
        index = frame.find(Command.SFD)
        if index == -1:
            print(f"{Print.ERROR}Don't find SFD(0xAA){Print.RESET}")
            return None
        else:
            return frame[index:]           
    
    @staticmethod
    def calc_crc(data: bytes) -> bytes:
        crc = data[0]
        for dt in data[1:]:
            crc ^= dt
        return crc.to_bytes(1, 'big')
    
    @staticmethod
    def check_crc(data: bytes) -> bool:
        received_crc = data[-1].to_bytes(1, 'big')
        collect_crc = Command.calc_crc(data[:-1])
        if received_crc == collect_crc:
            return True
        else:
            print(f"{Print.ERROR} CRC error !")
            print(f"\t-> received crc: {int.from_bytes(received_crc):02X}")
            print(f"\t   collect crc : {int.from_bytes(collect_crc):02X}")
            return False

    @staticmethod
    def analyze_frame(frame: bytes) -> None:
        frame = Command.check_SFD(frame)
        if frame != None:
            Command.check_crc(frame[1:])
        return



# role of communications in general
class Communication:
    retransmit_time = setting["retransmit_time"]
    timeout = setting["timeout"]

    def __init__(self):
        self.ser = None

    def select_port(self):
        print('Select using port')
        while True:
            ports = list(serial.tools.list_ports.comports())
            if not ports:
                input('No port found. Press any key to retry.')
                continue
            for i, port in enumerate(ports):
                print(f'{i:X}) {port.device}  ', end='\t')
            print()
            while True:
                choice_str = input('> ')
                if re.fullmatch(f'^[0-{len(ports)-1}]{{1}}$', choice_str):
                    choice = int(choice_str)
                    try:
                        self.ser: serial.Serial = serial.Serial(ports[choice].device, baudrate=9600, timeout=1)
                    except serial.SerialException as e:
                        print(e)
                        continue
                    return
    
    def transmit(self, frame: bytes) -> None:
        self.ser.write(frame)

    def receive(self) -> bytes | None:
        start_time = time.time()
        while time.time() - start_time < Communication.timeout:
            if self.ser.in_waiting > 0:
                    time.sleep(1.0) # wait for full data receive # TODO: coding more smart
                    response = self.ser.read_all()
                    return response
            time.sleep(0.1) # rest for cpu
        return None

    def close(self):
        if self.ser:
            self.ser.close()

def close_and_exit(com) -> None:
    com.close()
    print(f"Software exit.")
    sys.exit()


def main():
    print(f'\n=============================')
    print(f'=== {Print.BOLD}CMD Transmitter v1.00{Print.RESET} ===')
    print(f'=============================\n')

    com = Communication()
    com.select_port()
    cmd = Command()
    # cmd.select_device()

    print(f"\n{Print.LINE}\n")
    print(f"Enter any bytes in hex {Print.BOLD}(device ID, frame ID, payload){Print.RESET}")
    print(f"* Enter 'exit' to exit this software")
    while True:
        send_payload = cmd.input_payload(com)
        send_frame = cmd.make_frame(send_payload)
        receive = None
        for _ in range(Communication.retransmit_time+1):
            Print.transmit(send_frame)
            com.transmit(send_frame)
            receive = com.receive()
            if receive != None:
                break
        if receive != None:
            Print.receive(receive)
            cmd.analyze_frame(receive)
        else:
            print(f"PC didn't receive any signal")

if __name__ == '__main__':
    main()