import cv2
import numpy as np

def convertUnits(pixels):
    cmPerPix = 4.33/75  # 11 cm, or ~4.33 inches
    return pixels * cmPerPix

class cameraManager:
    def __init__(self, camCode, traceColor):
        self.cameraCode = camCode
        self.traceColor = traceColor
        self.vid = None
        self.currFrame = None
        self.bounds = [[110, 255, 255], [91,  100, 100]] # Blue range in HSV
        self.labels = ["Base", "Mid", "Piece"]
    
    def deinit(self):
        self.vid.release()
        cv2.destroyAllWindows()

    def beginCapture(self):
        self.vid = cv2.VideoCapture(self.cameraCode)
        if not self.vid.isOpened():
            return False
        return True

    def readFrame(self):
        ret, frame = self.vid.read()  # Read a frame from the video
        self.currFrame = frame
        return ret

    def identifyCoordinates(self):
        newCenters = {"Base":[0, 0], "Mid":[0, 0], "Piece":[0, 0]}
        
        # Identify contours of the specified color in the image, and determine the area of each
        newContours = self.trace_objects()

        if newContours is not False:
            cv2.drawContours(self.currFrame, newContours, -1, self.traceColor, 2)
            i = 0
            for contour in newContours:
                area, cX, cY = self.getContourCenter(contour)
                if area is not None:
                    cv2.circle(self.currFrame, (cX, cY), 7, (255, 0, 0), -1)
                    cv2.putText(self.currFrame, self.labels[i], (cX - 20, cY - 20),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    newCenters[self.labels[i]] = [cX, cY]
                    i += 1

        # Draw the center coordinates on the image
        i = 0
        coordList = list(newCenters.values())
        for coords in coordList:
            self.displayHeader(coords[0], coords[1], self.labels[i], 20*i + 15)
            i += 1

        return newCenters

    # Function to trace the three biggest objects of a certain color in a frame
    def trace_objects(self):
        if self.currFrame is not None:
            hsv = cv2.cvtColor(self.currFrame, cv2.COLOR_BGR2HSV)                         # Convert from BGR to HSV color space
            mask = cv2.inRange(hsv, np.array(self.bounds[1]), np.array(self.bounds[0]))   # Mask to extract the colored regions
            blurred_mask = cv2.GaussianBlur(mask, (5, 5), 0)                              # Gaussian blur for smoothing
            _, thresholded = cv2.threshold(blurred_mask, 50, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # Find contours in the mask

            # Make a list of the areas of each contour
            areas = []
            for con in contours:
                areas.append(cv2.contourArea(con))

            # Identify the three biggest contours and return them
            lim = min(3, len(areas))    
            bigCons = []
            for _ in range(lim):
                maxIndex = areas.index(max(areas))
                bigCons.append(contours[maxIndex])
                areas[maxIndex] = 0
            return bigCons
        return False

    # Return the area and centroid coordinates of a contour
    def getContourCenter(self, c):
        M = cv2.moments(c)
        area = cv2.contourArea(c)
        if area > 10:
            if M["m00"] != 0:
                cX = int(M['m10']/M['m00'])
                cY = int(M['m01']/M['m00'])
            else:
                cX, cY = 0, 0
            return area, cX, cY
        return None, 0, 0
    
    def displayHeader(self, cX, cY, color, startY):
        cmX = convertUnits(cX)
        cmY = convertUnits(cY)
        text = color + ": " + f"({cX}, {cY}) pixels =" + " ({:.2f}, {:.2f}) cm".format(cmX, cmY) 
        cv2.putText(self.currFrame, text, (0, startY) ,cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def displayFrame(self):
        if self.currFrame is not None:
            cv2.imshow('Eagle Eye', self.currFrame) # Display the resulting frame
    
    def detectKeys(self):
        if cv2.waitKey(25) & 0xFF == ord('q'): # Break the loop when 'q' key is pressed
            return 'q'
        if cv2.waitKey(25) & 0xFF == ord(' '):
            return ' '
