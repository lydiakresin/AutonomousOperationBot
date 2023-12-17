from machine import Pin
import time

class Stepper():
    def __init__(self, pin1Num, pin2Num, pin3Num, pin4Num, angle):
        self.pin1 = Pin(pin1Num, Pin.OUT)
        self.pin2 = Pin(pin2Num, Pin.OUT)
        self.pin3 = Pin(pin3Num, Pin.OUT)
        self.pin4 = Pin(pin4Num, Pin.OUT)
        self.pinList = [self.pin1, self.pin2, self.pin3, self.pin4]
        self.stepSeq = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
        self.revrSeq = [[0,0,0,1],[0,0,1,0],[0,1,0,0],[1,0,0,0]]
        self.currAngle = angle
        self.degToLoop = 128/90  # 128 loop iterations is 90 degrees, ~ 1.42 loops/degree
        self.loopToDeg = 90/128  # the inverse, ~ 0.703 degrees/loop

    def stepLoop(self, stepList):
        for step in stepList:
            for i in range(len(self.pinList)):
                self.pinList[i].value(step[i])
                time.sleep(0.001)
    
    def turnToAngle(self, endAngle):  # RECEIVES ANGLE IN DEGREES
        angleDiff = endAngle - self.currAngle           # Check this later with some negative values
        loopNum = int(abs(angleDiff * self.degToLoop))  # Casting to an int will make it a bit less accurate
        if angleDiff > 0:
            self.counterClockwise(loopNum)
        elif angleDiff < 0:
            self.clockwise(loopNum)
        self.stop()
        return 0
    
    def clockwise(self, loopNum):
        for i in range(loopNum):
            self.stepLoop(self.stepSeq)
            self.currAngle -= self.loopToDeg
    
    def counterClockwise(self, loopNum):
        for i in range(loopNum):
            self.stepLoop(self.revrSeq)
            self.currAngle += self.loopToDeg
    
    def stop(self):
        for pin in self.pinList:
            pin.value(0)
        
