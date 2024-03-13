import network
import urequests
import json
from time import sleep, ticks_ms, ticks_diff
from machine import Pin, reset
from picozero import pico_led
import utime


# Setup pin 18 (Request-send pin) as input:
request_switch = Pin(18, Pin.IN, Pin.PULL_DOWN)

# Setup pin 16 (Reset pin) as input:
restart_button = Pin(16, Pin.IN, Pin.PULL_UP)

# Setup pin 17 as restart status LED:
restart_status_led = Pin(17, Pin.OUT)


# Function to fast-blink `pico_led`:
def led_fast_blink(led, cycles):
    for _ in range(cycles):
        led.on()
        sleep(0.1)
        led.off()
        sleep(0.1)


# Define a callback function to reset the Pico:
def restart_pico(pin):
    print("We're trying to restart this thing...")
    led_fast_blink(restart_status_led, 4)
    sleep(0.5)
    reset()


# Attach interrupt to Restart pin:
restart_button.irq(trigger=Pin.IRQ_FALLING, handler=restart_pico)


# Function to load WiFi credentials from `config.json`:
def load_config(file_path):
    """
    Load a JSON configuration file and return it as a dictionary.
    """
    with open(file_path, "r") as f:
        config = json.load(f)
    return config


# Get the configuration settings from the config.json file:
config = load_config("config.json")
# Set the ssid and password from the configuration settings:
ssid = config["ssid"]
password = config["password"]
print("Loaded WiFi Settings!")


url_on = "http://192.168.4.1:8000/gpio/on"
url_off = "http://192.168.4.1:8000/gpio/off"

# Setup WiFi connection
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# Wait for connection
while not wlan.isconnected():
    pass

print("Connected to WiFi!")
led_fast_blink(pico_led, 10)


# Define a callback function to send the request:
def send_request(pin):
    if pin.value() == 1:
        # Pin went high, turn on the LED
        print("Sending request to turn on LED")
        urequests.get(url_on).close()
        led_fast_blink(pico_led, 5)
    else:
        # Pin went low, turn off the LED
        print("Sending request to turn off LED")
        urequests.get(url_off).close()
        pico_led.on()
        sleep(1)
        pico_led.off()


# Attach interrupt to Request-send pin:
request_switch.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=send_request)