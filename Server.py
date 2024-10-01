import platform

if platform.system() != "Windows":
    print("This script only works on Windows.")
    exit()

import socket
import json
import pydirectinput
import time
from enum import Enum

####################################################

# mode0 = 854x480, mode1 = 1280x720
GAMEPAD_TP_MODE = "mode0" 

SMOOTHING_FACTOR = 0.1
SPEED_MULTIPLIER = 10 

# Timeout in seconds for disconnected clients
TIMEOUT = 5

####################################################

# https://wut.devkitpro.org/group__vpad__input.html
# https://github.com/devkitPro/wut/blob/master/include/vpad/input.h
class VPADButtons(Enum):
    VPAD_BUTTON_ZL = 0x0080
    VPAD_BUTTON_L = 0x0020

# Wii U Gamepad touch screen resolution
# (This is the resolution of the touch screen setting from the MiiSendU Wii U app code, by default "mode0")
def get_Gamepad_resolution(mode):
    if mode == 'mode0':
        return (854, 480)
    elif mode == 'mode1':
        return (1280, 720)
    else:
        return (854, 480)

GAMEPAD_WIDTH, GAMEPAD_HEIGHT = get_Gamepad_resolution(GAMEPAD_TP_MODE)

# PC resolution
OUTPUT_WIDTH, OUTPUT_HEIGHT = pydirectinput.size()

# Left Click 
def leftClick(mode):
    if mode == "down":
        pydirectinput.mouseDown(None, None, 'left')
    elif mode == "up":
        pydirectinput.mouseUp(None, None, 'left')

# Get local IP
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    finally:
        s.close()
    return ip_address

print("\nMiiSendU Server -- by Trock and Slushi\n")

# Start server
PORT = 4242
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (get_local_ip(), PORT)
print('starting server on {} port {}'.format(*server_address))
sock.bind(server_address)

clients = {}
print("\nWaiting for clients...")

pydirectinput.FAILSAFE = False
pydirectinput.PAUSE = 0

button_pressed = False

# Main loop
while True:
    try:
        sock.settimeout(1)
        try:
            data, address = sock.recvfrom(4096)
            current_time = time.time()
            if address not in clients:
                clients[address] = {"lastPosition": None, "lastTime": current_time}
                print("[Client {}] - Wii U Gamepad connected!".format(address))
            else:
                clients[address]["lastTime"] = current_time

                if len(clients[address]) > 2:
                    print("This program only supports one client at a time.")
                    exit(1)

            decodedData = json.loads(data)
            vpad = decodedData["wiiUGamePad"]

            # Move cursor
            if vpad["tpTouch"]:
                # Scale the touch coordinates
                scaled_x = int(vpad["tpX"] / GAMEPAD_WIDTH * OUTPUT_WIDTH)
                scaled_y = int(vpad["tpY"] / GAMEPAD_HEIGHT * OUTPUT_HEIGHT)

                current_x, current_y = pydirectinput.position()

                cursor_x = int((scaled_x) * SMOOTHING_FACTOR * SPEED_MULTIPLIER)
                cursor_y = int((scaled_y) * SMOOTHING_FACTOR * SPEED_MULTIPLIER)

                pydirectinput.moveTo(cursor_x, cursor_y, relative=True)

            # Click
            if vpad["hold"] & VPADButtons.VPAD_BUTTON_ZL.value or vpad["hold"] & VPADButtons.VPAD_BUTTON_L.value:
                if not button_pressed:
                    leftClick("down")
                    button_pressed = True
            else:
                leftClick("up")
                button_pressed = False

        except socket.timeout:
            pass

            current_time = time.time()
            disconnected_clients = [addr for addr, client in clients.items() if current_time - client["lastTime"] > TIMEOUT]
            for addr in disconnected_clients:
                print(f"Client {addr} disconnected due to timeout.")
                time.sleep(1)
                print("Finishing program...")
                exit(1)
    except KeyboardInterrupt:
        sock.close()
        print("Program finished!")
        break