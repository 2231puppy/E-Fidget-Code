import time

import alarm

from neopixel import NeoPixel, GRB
from adafruit_debouncer import Button
import board
import digitalio as dio
import pwmio

NUM_PIXELS = 30 # This is a hack to make the transition smoother
ORDER = GRB

pixels = NeoPixel(
    board.NEOPIXEL, NUM_PIXELS, brightness=0.03, auto_write=False, pixel_order=ORDER
)

m1 = pwmio.PWMOut(board.M1, frequency=1000)
m2 = pwmio.PWMOut(board.M2, frequency=1000)
m3 = pwmio.PWMOut(board.M3, frequency=1000)
m4 = pwmio.PWMOut(board.M4, frequency=1000)
m5 = pwmio.PWMOut(board.M5, frequency=1000)
m6 = pwmio.PWMOut(board.M6, frequency=1000)
m7 = pwmio.PWMOut(board.M7, frequency=1000)
m8 = pwmio.PWMOut(board.M8, frequency=1000)

b1 = dio.DigitalInOut(board.BTN1)
b2 = dio.DigitalInOut(board.BTN2)
b3 = dio.DigitalInOut(board.BTN3)

b1.switch_to_input()
b1.pull = dio.Pull.UP

b2.switch_to_input()
b2.pull = dio.Pull.UP

b2 = Button(b2)

b3.switch_to_input()
b3.pull = dio.Pull.UP

motors = [m1, m2, m3, m4, m5, m6, m7, m8]


def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b)

def fast_spin():
    for i in range(5, 13):
        if b3.value == 0:
            cycles_since_presses = 0
            return 0
        if b1.value == 0:
            while b1.value == 0:
                pass
            return 1
        for motor in motors:
            if b1.value == 0:
                while b1.value == 0:
                    pass
                return 1
            if b3.value == 0:
                cycles_since_presses = 0
                return 0
            motor.duty_cycle = 65535
            time.sleep(0.04)
            motor.duty_cycle = 0
            time.sleep(i / 100)
    return 0


def breathe():
    for cycle in range(10, 15, 1):
        for motor in motors:
            if b3.value == 0:
                cycles_since_presses = 0
                return 0
            motor.duty_cycle = cycle * 1000
            time.sleep(0.1)
    for i in range(5):
        if b3.value == 0:
            cycles_since_presses = 0
            return 0
        for motor in motors:
            motor.duty_cycle = 60000
        time.sleep(0.03)
        for motor in motors:
            motor.duty_cycle = 0
        time.sleep(1)
    for cycle in range(20, 10, -2):
        for motor in motors:
            if b3.value == 0:
                cycles_since_presses = 0
                return 0
            motor.duty_cycle = cycle * 1000
            time.sleep(0.1)
    for motor in motors:
        motor.duty_cycle = 0
    return 0


mode = 0

modes = [fast_spin, breathe]

cycles_since_presses = 0

leds_enabled = False

while True:
    if leds_enabled:
        for j in range(255):
            if b1.value == 0:
                cycles_since_presses = 0
                continue
            for i in range(NUM_PIXELS):
                pixel_index = (i * 256 // NUM_PIXELS) + j
                pixels[i] = wheel(pixel_index & 255)
            pixels.show()
            time.sleep(0.002)
            b2.update()
            if b2.long_press:
                b2.update()
                cycles_since_presses = 0
                leds_enabled = not leds_enabled
                break
            elif b2.short_count >= 1:
                cycles_since_presses = 0
                if mode + 1 == len(modes):
                    mode = 0
                else:
                    mode += 1
                print(mode)
                break
    else:
        pixels.fill((0, 0, 0))
        pixels.show()
        for tick in range(255):
            b2.update()
            if b2.long_press:
                b2.update()
                cycles_since_presses = 0
                leds_enabled = not leds_enabled
                continue
            elif b2.short_count >= 1:
                cycles_since_presses = 0
                if mode + 1 == len(modes):
                    mode = 0
                else:
                    mode += 1
                print(mode)
            time.sleep(0.002)
            if b1.value == 0:
                cycles_since_presses = 0
                exit_code = modes[mode]()
                while exit_code != 0:
                    exit_code = modes[mode]()
    if b1.value == 0:
        cycles_since_presses = 0
        exit_code = modes[mode]()
        while exit_code != 0:
            exit_code = modes[mode]()

    cycles_since_presses += 1
    if cycles_since_presses > 45:
        break
    b2.update()

pixels.fill((0, 0, 0))
pixels.show()
b1.deinit()
b3.deinit()
alarm_b1 = alarm.pin.PinAlarm(pin=board.BTN1, value=False, pull=True)
alarm_b3 = alarm.pin.PinAlarm(pin=board.BTN3, value=False, pull=True)
alarm.exit_and_deep_sleep_until_alarms(alarm_b1, alarm_b3)
