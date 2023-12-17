
#import cv2
import numpy as np
import paho.mqtt.client as mqtt
from cameraManager import cameraManager
import time

cameraCode = 0  # 0 is phone cam, 1 is webcam

broker_address = '10.243.39.227'
channel = "tristan"
sendActive = False

stableTimeThresh = 30 # Frame cutoff for determining if the piece is stable 
stablePixlThresh = 5  # Pixel cutoff for determining if the piece is stable
distThresh = 10       # Pixel cutoff for identifying that the piece moved 

def zeroCenters(centers):
    origin = centers["Base"]
    zeroOut = lambda x: [x[0] - origin[0], x[1] - origin[1]]
    for key in centers:
        centers[key] = zeroOut(centers[key])
    return centers

def startClient():
    client = mqtt.Client("computer")
    #client.on_message = callback
    client.connect(broker_address)
    client.loop_start()
    return client
    
def sendData(client, data, channel):
    client.publish(channel, str(data))
    print("Message sent")

def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def swapCoords(coords):
    newCoords = [coords[1], coords[0]]
    return newCoords

def main():
    if sendActive:
        client = startClient()

    traceColor = (255, 0, 0)
    camManager = cameraManager(cameraCode, traceColor)

    check = camManager.beginCapture()
    if not check:
        print("Cannot open camera")
        exit()
    else:
        print("Video feed live")

    beginCollection = False
    stableCount = 0
    currentSent = False

    oldCenters = {"Base":[0, 0], "Mid":[0, 0], "Piece":[0, 0]}
    
    SEARCHING = 1
    MOVING    = 2
    ZEROING   = 3
    FOUND     = 4
    state = SEARCHING

    checkSpot = [75, 95] # Pre-chosen location for calibration spot
    start = [0, 0]

    while True:
        ret = camManager.readFrame()
        if not ret:
            break
        
        newCenters = camManager.identifyCoordinates()

        if beginCollection:
            pieceDist = distance(newCenters["Piece"], oldCenters["Piece"])
            if pieceDist < stablePixlThresh:
                stableCount += 1
            else:
                if int(pieceDist) <= 200 and pieceDist > distThresh:
                    stableCount = 0

            if stableCount > stableTimeThresh:
                if state == SEARCHING:
                    print("\nStable Position Identified:", newCenters["Piece"])
                    print("Deploying arm")
                    if not startFound:
                        start = newCenters["Piece"]
                        startFound = True
                    if sendActive:
                        sendData(client, SEARCHING, "state") # sending state as searching
                        zeroedCenters = zeroCenters(newCenters)
                        pieceCenter = zeroedCenters["Piece"]
                        sendData(client, swapCoords(pieceCenter), "coords")
                    state = MOVING
                    stableCount = 0

                elif state == MOVING:
                    print("\nArm movement complete")
                    print("Repositioning to test location")
                    if sendActive:
                        sendData(client, MOVING, "state")
                        sendData(client, checkSpot, "coords")
                    state = ZEROING
                    stableCount = 0
                
                elif state == ZEROING:
                    if sendActive:
                        sendData(client, ZEROING, "state")
                    print("\nZeroing complete- confirming distance")
                    pieceDist = distance(start, newCenters["Piece"])
                    print(f"Distance: {pieceDist}\n")
                    if pieceDist > 200:
                        state = FOUND
                        print("Distance Acceptable- PIECE FOUND")
                        if sendActive:
                            sendData(client, FOUND, "state")
                            sendData(client, "Piece found", "done")
                        break
                    else:
                        print("Distance unacceptable- no significant difference.")
                        print("Search mode re-engaged")
                        state = SEARCHING
                        stableCount = 0
        
        camManager.displayFrame()
        keyCode = camManager.detectKeys()
        if keyCode == 'q':
            break
        elif keyCode == ' ':
            print("DATA COLLECTION ACTIVE")
            beginCollection = True
            armLen = distance(newCenters["Base"], newCenters["Mid"])
            if sendActive:
                print("Sending arm length:", armLen)
                sendData(client, str(armLen), "arms")
        
        for key in newCenters:
            oldCenters[key] = newCenters[key]

    # Release the video capture object and close all windows
    camManager.deinit()

main()