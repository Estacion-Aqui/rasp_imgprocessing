import cv2, os, pytesseract, datetime, time, imutils, re
from pathlib import Path
from sys import platform
import numpy as np
import matplotlib.pyplot as plt

class OpenCvProcess:

  imageSource = ""

  def __init__(self):
      if platform == "win32":
          pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"


  def findPossiblePlatesContours(self):
    img = cv2.imread(self.imageSource)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    sobelx      = cv2.Sobel(blurred,cv2.CV_8U,1,0,ksize=3,scale=1,delta=0,borderType=cv2.BORDER_DEFAULT)
    isobelx = cv2.Sobel(blurred, cv2.CV_8U, 1, 0, 3)
    sobely      = cv2.Sobel(blurred,cv2.CV_8U,0,1,ksize=3,scale=1,delta=0,borderType=cv2.BORDER_DEFAULT)

    tmp, imgThs = cv2.threshold(sobelx,0,255,cv2.THRESH_OTSU+cv2.THRESH_BINARY)
    morph       = cv2.getStructuringElement(cv2.MORPH_RECT,(40,10))
    plateDetect = cv2.morphologyEx(imgThs,cv2.MORPH_CLOSE,morph)
    regionPlate = plateDetect.copy()

    contours = cv2.findContours(regionPlate.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    contours = sorted(contours,key=cv2.contourArea, reverse = True)[:5]

    return contours


  def preProcessPlateImage(self, img_roi):
    if img_roi is None:
      return

    kernel = np.ones((1, 1), np.uint8)

    resize_img_roi = cv2.resize(img_roi, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
    img_grey = cv2.cvtColor(resize_img_roi, cv2.COLOR_BGR2GRAY)

    rgb_planes = cv2.split(img_grey)

    result_norm_planes = []
    for plane in rgb_planes:
      dilated_img = cv2.dilate(plane, np.ones((12, 12), np.uint8))
      bg_img = cv2.medianBlur(dilated_img, 21)
      diff_img = 255 - cv2.absdiff(plane, bg_img)
      norm_img = cv2.normalize(diff_img,None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
      result_norm_planes.append(norm_img)

    result_norm = cv2.merge(result_norm_planes)

    img_blur = cv2.GaussianBlur(result_norm, (5, 5), 0)
    img_dilate = cv2.dilate(img_blur, kernel, iterations=3)
    img_erode = cv2.erode(img_dilate, kernel, iterations=3)

    _, img_binary = cv2.threshold(img_erode, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return img_binary


  def handleChars(self, plateChar):
    return {
      'A': '1', 'B': '8', 'C': 'C', 'D': 'D', 'E': '3', 'F': '3', 'G': '0', 'H': '4', 'I': '1', 'J': 'J', 'K': 'k', 'L': '4', 'M': 'M', 'N': 'N', 'O': '0', 'P': '9', 'Q': '0', 'R': '4', 'S': '5', 'T': '7', 'U': '0', 'V': 'V', 'W': 'W', 'X': 'X', 'Y': '9', 'Z': '7'
    }[plateChar.upper()]


  def handleNumbers(self, plateNum):
    return {
      '0': 'O', '1': 'L', '2': 'Z', '3': 'E', '4': 'L', '5': 'S', '6': 'G', '7': 'T','8': 'B', '9': '9'
    }[str(plateNum)]

  def handlePlate(self, plate):
    plateList = list(plate)

    for ind, c in enumerate(plate):
      if (ind == 0 or ind == 1 or ind == 2):
        plateList[ind] = self.handleNumbers(c) if c.isdigit() else c
      elif (ind == 3 or ind == 5 or ind == 6):
        plateList[ind] = self.handleChars(c) if c.isalpha() else c

    return ''.join(plateList)


  def checkPlateChars(self, plate):
    platechars = "".join(re.findall("[a-zA-Z0-9]", plate))

    if len(platechars) == 7:
      treatedPlate = self.handlePlate(platechars[0:7])

      return treatedPlate, True
    elif len(platechars) >= 7:
      treatedPlate = platechars[1:8] if platechars[0].islower() or platechars[0].upper() == "I" or platechars[0].upper() == "L" or platechars[0].upper() == "P" or platechars[0].upper() == "A" else platechars[0:7]
      treatedPlate = self.handlePlate(treatedPlate)

      return treatedPlate, True
    else:
      return "", False


  def ocrPlateImage(self, image):
    config = r'--psm 7 --oem 3'
    output = ""

    try:
      output = pytesseract.image_to_string(image, lang='eng', config=config)

    except Exception as e:
      print("falha ao ler imagem com o tesseract: " + str(e))
      return "", False
    else:
      checkedPlate, isPlate = self.checkPlateChars(output)
      return checkedPlate, isPlate


  def findLicensePlate(self, contours):
    img = cv2.imread(self.imageSource)
    foundPlateChars = []

    for index, c in enumerate(contours):
      perimeter = cv2.arcLength(c, True)
      approx = cv2.approxPolyDP(c, 0.03 * perimeter, True)
      (x, y, lar, alt) = cv2.boundingRect(c)

      roi = img[y:y + alt, x:x + lar]

      try:
        processedImage = self.preProcessPlateImage(roi)
      except Exception as e:
        print("falha ao processar imagem: " + str(e))
        continue

      plateChars, foundPlate = self.ocrPlateImage(processedImage)

      if (foundPlate):
        foundPlateChars.append(plateChars.upper())

    return foundPlateChars


  def cleanFiles(self):
    if Path(self.imageSource).is_file():
      os.remove(self.imageSource)


  def exec(self, imgSource):
    foundPlate = []

    try:
      self.imageSource = imgSource

      contours = self.findPossiblePlatesContours()
      foundPlate = self.findLicensePlate(contours)
    except Exception as e:
      print("falha no processo de leitura: " + str(e))

    self.cleanFiles()

    return str(foundPlate[0]) if len(foundPlate) > 0 else ""
