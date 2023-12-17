import math
import time
from machine import Pin
from LittleStepperClass import lilStepper
from BigStepperClass import BigStepper
from i2cScreenClass import i2cScreen
import mqtt
import network, ubinascii

coordinates = [] # coordinates of Operation game piece
# Declare variables for functions
x = 0
y = 0
d1 = 0 # length of arm 1
d2 = 0 # length of arm 2

ipaddress = "10.243.39.227" # Tufts ip address
received = False
found = False
coordsTop = "coords"
armsTop = "arms"
doneTop = "done"
stateTop = "state"

state = 0
currentState = 0
lastState = 0

screen = i2cScreen()

# ————————— Wifi setup —————————
def connect_wifi():
    station = network.WLAN(network.STA_IF)
    station.active(True)
    mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
    print("MAC " + mac)
    
    station.connect("Tufts_Wireless","")
    while not station.isconnected():
        time.sleep(1)
    print('Connection successful')
    print(station.ifconfig())
    
# ------------- STEPPER 1 SETUP (NEMA 17) --------------- #
# Pin assignments

bigStep = BigStepper(17, 18, 19, 20, 21, 0)  # 5 pins and current angle
smallStep = lilStepper(10, 11, 12, 13, 0)    # 4 pins and current angle

# ————————— mqtt subscribing —————————  
def whenCalled(topic, msg):
    global coordinates, received, d1, d2, found, currentState, screen
    top = topic.decode()
    message = msg.decode() # message is in form [[first arm coords], [second arm], [end effector]]
    print("message: ", message, " topic: ", top)
    
    if top == armsTop: # Getting length of arms in pixels
        print("arm length getting")
        armLength = float(message)
        print("Arm length: ", armLength)
        d1 = d2 = armLength
    
    elif top == coordsTop: # Getting coordinates of piece, change to "piece" (change channel in other code)
        coordSplit = message.strip('[]').split(',')
        coordinates.append(coordSplit)
        print("Coordinates: ", coordinates)
        received = True
    
    elif top == stateTop:
        currentState = int(message)
        screen.mainDisplay(currentState)
    
    elif top == doneTop:
        found = True
        state = 4
        print("Piece found")
        
    
# ------------- INVERSE KINEMATICS CALCULATIONS --------------- #

# Calculates the corresponding angles to an (x,y) point along a circle, with robotic arms
# of lengths d1 and d2. Assumes arms start at (0,0). Returns angles in degrees.
def invKinematics(coordinates, d1, d2):
    print(coordinates)
    x = float(coordinates[0]) # don't need to convert bc already in pixels
    y = -1*float(coordinates[1])
    print("x, y: ", x,y)
    L = math.sqrt(x**2 + y**2)
    try:
        gamma2 = math.acos((d1**2+L**2-d2**2)/(2*d1*L))
        gamma1 = math.acos((d1**2+d2**2-L**2)/(2*d1*d2))
    except:
        print("Math domain error")
        time.sleep(.1)
        angles = None
        pass
        
    theta = math.atan2(y,x) - gamma2 # theta is angle relative to ground
    alpha = math.pi - gamma1 # alpha is angle relative to first arm
    theta = -1*math.degrees(theta)
    alpha = -1*math.degrees(alpha)
    return [theta, alpha]

def moveArm1(angles):
    global currentTheta, bigStep
    desiredTheta = angles[0]
    print("Theta: ", desiredTheta)
    thetaDiff = desiredTheta - bigStep.currentTheta
    bigStep.turnToAngle(thetaDiff, desiredTheta)

def moveArm2(angles):
    global currentAlpha, smallStep
    desiredAlpha = angles[1]
    print("Alpha: ", desiredAlpha)
    alphaDiff = desiredAlpha - smallStep.currAngle
    smallStep.turnToAngle(alphaDiff)

def main():
    # Set up wifi and mqtt
    connect_wifi()
    try:
        broker = mqtt.MQTTClient("lydia", ipaddress, keepalive=600)
        broker.connect()
        broker.set_callback(whenCalled)
        print('Broker connected')
    except OSError as e:
        print('Failed')
        return

    broker.subscribe(armsTop)
    broker.subscribe(coordsTop) # subscribing to topic to receive coordinates
    broker.subscribe(doneTop)
    broker.subscribe(stateTop)
    bigStep.EN_pin.value(0)  # Pull enable pin low to allow motor control
    
    currentState = 0
    lastState = 0
    screen.mainDisplay(currentState)
    
    while True:
        while len(coordinates) > 0:
            # Inverse kinematics to find required arm angles
            angles = invKinematics(coordinates[0],d1,d2) # coordinates received from broker
            if angles is not None:
                print("Angles: ", angles)
                # Move arms
                moveArm1(angles)
                moveArm2(angles)
                coordinates.remove(coordinates[0])

            broker.check_msg()
            time.sleep(.01)        
        
        if found == True:
            print("Operation successful")
            bigStep.reset_ED_pins()
            print("Resetting pins")
            break
            # Make LED blink
    
        broker.check_msg()
        time.sleep(.01)

    bigStep.reset_ED_pins()
    print("reset pins")
    screen.mainDisplay(4)
    
main()
        
"""
    # -- Replace with coordinates from camera
    xUser = input("Enter number for x position:\n")
    yUser = input("Enter number for y position:\n")
    xVal = int(xUser)
    yVal = int(yUser)
    coordinates = [xVal, yVal]
"""