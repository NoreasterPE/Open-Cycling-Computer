import RPi.GPIO as GPIO
import time


# class mma8451(threading.Thread):
class mma8451():

    'Class for MMA8451 Triple-Axis Accelerometer w/ 14-bit ADC with I2C interface as sold by Adafruit'
    # def __init__(self, occ, simulate = False):

    def __init__(self):
        # Setup Raspberry PINS, as numbered on BOARD
        self.SCL = 38  # GPIO for SCL
        self.SDA = 40  # GPIO for SDA

        # SCL frequency 100 kHz
        self.delay = 1 / 100000.0
        # self.set_up_gpio()
    # def set_up_gpio(self):
        # self.l.debug("[BMP] set_up_gpio")
        # GPIO initialisation
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.SCL, GPIO.OUT, initial=GPIO.HIGH,
                   pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.SDA, GPIO.OUT, initial=GPIO.HIGH,
                   pull_up_down=GPIO.PUD_UP)
        # i2c start
        GPIO.output(self.SDA, 1)
        time.sleep(self.delay)
        GPIO.output(self.SCL, 1)
        time.sleep(self.delay)
        GPIO.output(self.SDA, 0)
        time.sleep(self.delay)
        GPIO.output(self.SCL, 0)
        time.sleep(self.delay)

        GPIO.setup(self.SCL, GPIO.OUT, initial=GPIO.LOW,
                   pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.SDA, GPIO.OUT, initial=GPIO.LOW,
                   pull_up_down=GPIO.PUD_UP)

        # i2c stop
        GPIO.output(self.SDA, 0)
        time.sleep(self.delay)
        GPIO.output(self.SCL, 1)
        time.sleep(self.delay)
        GPIO.output(self.SDA, 1)
        time.sleep(self.delay)

mma8451 = mma8451()
