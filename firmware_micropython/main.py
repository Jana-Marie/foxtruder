from machine import Pin, I2C, PWM, ADC
import time
import neopixel

# Board Constants
LED_READY = 0
LED_VALVE = 3
LED_HOTEND = 1
LED_ERROR = 2

LED_SK6812 = Pin(8)

ADC_TEMP = Pin(2)

PWM_PIN_VALVE = Pin(0)
PWM_PIN_HOTEND = Pin(1)

I2C0_SCL = Pin(4)
I2C0_SDA = Pin(5)
I2C0_PCA9536_ADDR = 65

BUTTON_FUNC = Pin(6, Pin.IN, Pin.PULL_UP)
BUTTON_TRIG = Pin(7, Pin.IN, Pin.PULL_UP)

# State
ledState = 0
error = False
active = False
i2c = None
hotend = None
valve = None
tempsens = None
rgbLeds = None

def setBit(v, index, x):
    mask = 1 << index
    v &= ~mask
    v |= x << index
    return v

def initHardware():
    global i2c, hotend, valve, tempsens, rgbLeds

    # LEDs on PCA9536 IO Expander
    #i2c = I2C(0, scl=I2C0_SCL, sda=I2C0_SDA)
    # intialize pins as outputs
    #i2c.writeto(I2C0_PCA9536_ADDR, bytes([0x03, 0x00]))
    # disable all LEDs
    #i2c.writeto(I2C0_PCA9536_ADDR, bytes([0x01, ledState]))

    # SK6812 LEDs
    rgbLeds = neopixel.NeoPixel(LED_SK6812, 5, 3)

    # PWM
    # Hotend
    hotend = PWM(PWM_PIN_HOTEND, freq=20000, duty_u16=512)
    hotend.duty(0)
    # Valve
    valve = PWM(PWM_PIN_VALVE, freq=20000, duty_u16=512) 
    valve.duty(0)

    # Temperature Sensor
    tempsens = ADC(ADC_TEMP, atten=ADC.ATTN_11DB)

    # Set button interrupt handler
    BUTTON_TRIG.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=handleTrigPress)
    BUTTON_FUNC.irq(trigger=Pin.IRQ_RISING, handler=handleFuncPress)

def listenSocket():
    import socket
    addr = socket.getaddrinfo('0.0.0.0', 1337)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    conn,addr = s.accept()
    conn.send("meow\n")
    conn.close()

def handleFuncPress(pin):
    global active, error
    if not active or error:
        print("Function button pressed, activating..")
        active = True
        error = False
        setLED(LED_READY, 1)

def handleTrigPress(pin):
    time.sleep(0.01)
    if pin.value():
        setValve(False)
    else:
        setValve(True)

def setLED(ledIndex, val):
    global ledState

    ledState = setBit(ledState, ledIndex, val)
    #i2c.writeto(I2C0_PCA9536_ADDR, bytes([0x01, ledState]))

def setHotend(value):
    global hotend

    print(f"Setting hot end to {value}")
    if value == 0:
        setLED(LED_HOTEND, 0)
    else:
        setLED(LED_HOTEND, 1)
    hotend.duty(value)

def setValve(value):
    global valve

    print(f"Setting valve to {value}")
    if value:
        setLED(LED_VALVE, 1)
        valve.duty(250)
    else:
        setLED(LED_VALVE, 0)
        valve.duty(0)

def readTemp():
    global tempsens
    return tempsens.read_uv()

def convertTemp(rawTemp):
    poly1 = 1.79E-04 * rawTemp
    poly2 = -8.8E-11 * rawTemp ** 2
    poly3 = 2.04E-17 * rawTemp ** 3
    return 23 + poly1 + poly2 + poly3

initHardware()

rgbLeds.fill(bytes([30, 6, 0]))
rgbLeds.write()
 
setHotend(0)

while True:
    temp = convertTemp(readTemp())
    print(f"Raw Temperature: {readTemp()}")
    print(f"Temperature: {temp}")

    if temp > 230:
        setHotend(0)
        setValve(False)
        setLED(LED_READY, 0)
        setLED(LED_ERROR, 1)
        print("Error, stopping operation")
        break

    tTarget = 220
    tReal = temp
    tDelta = tTarget - tReal

    if active and not error:
        if tDelta > 30:
            setHotend(1023)
        elif tDelta > 5:
            if BUTTON_TRIG.value():
                setHotend(800)
            else:
                setHotend(1000)
        elif tReal < tTarget and tDelta > -5:
            if BUTTON_TRIG.value():
                setHotend(160)
            else:
                setHotend(254)
        else:
            setHotend(0)

    time.sleep(0.5)


