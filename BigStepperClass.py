from machine import Pin
import time

class BigStepper():
    def __init__(self, stpPin, dirPin, MS1Pin, MS2Pin, ENPin, theta):
        # Default 17, 18, 19, 20, 21
        self.stp_pin = Pin(stpPin, Pin.OUT)
        self.dir_pin = Pin(dirPin, Pin.OUT)
        self.MS1_pin = Pin(MS1Pin, Pin.OUT)
        self.MS2_pin = Pin(MS2Pin, Pin.OUT)
        self.EN_pin  = Pin(ENPin,  Pin.OUT)
        self.stepsPerRev = 1600 # because using 1/8 stepper mode
        self.currentTheta = theta

    
    def turnToAngle(self, angle):
        print("Stepping at 1/8th microstep mode.")
        self.MS1_pin.value(1)
        self.MS2_pin.value(1)
        numSteps = theta*(self.stepsPerRev/360)
        print("NumSteps: ", numSteps)
        if numSteps > 0:
            self.dir_pin.value(0)
        elif numSteps < 0:
            self.dir_pin.value(1)
        self.turnMotor(abs(numSteps))
    
    def turnMotor(self, numSteps):
        for x in range(numSteps):
            self.stp_pin.value(1)
            time.sleep_us(1000)
            self.stp_pin.value(0)
            time.sleep_us(1000)
        
    def reset_ED_pins(self):
        self.stp_pin.value(0)
        self.dir_pin.value(0)
        self.MS1_pin.value(0)
        self.MS2_pin.value(0)
        self.EN_pin.value(1)
