import cv2, os, pytesseract, datetime, time
from pathlib import Path
import imutils
import numpy as np
import re

class OpenCvProcess:

  #pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

  imageSource = ""

  spot_number = ""

  def findPossiblePlatesContours(self):
    img = cv2.imread(self.imageSource)
    element = cv2.getStructuringElement(cv2.MORPH_RECT, (22, 3))

    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    grey = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    
    sobelx = cv2.Sobel(grey, cv2.CV_8U, 1, 0, 3)
    _, threshold_img = cv2.threshold(sobelx, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    morph_n_thresholded_img = threshold_img.copy()
    cv2.morphologyEx(src = threshold_img, op = cv2.MORPH_CLOSE, kernel = element, dst = morph_n_thresholded_img)
    morph_n_thresholded_img = cv2.erode(morph_n_thresholded_img, None, iterations=2)
    morph_n_thresholded_img = cv2.dilate(morph_n_thresholded_img, None, iterations=2)

    contours = cv2.findContours(morph_n_thresholded_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    contours = sorted(contours,key=cv2.contourArea, reverse = True)[:5]

    return contours


  def preProcessPlateImage(self, img_roi):
    if img_roi is None:
      return

    resize_img_roi = cv2.resize(img_roi, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    img_grey = cv2.cvtColor(resize_img_roi, cv2.COLOR_BGR2GRAY)
    _, img_binary = cv2.threshold(img_grey, 70, 255, cv2.THRESH_BINARY)
    blurred_img = cv2.GaussianBlur(img_binary, (5, 5), 0)

    return blurred_img


  def checkPlateChars(self, plate):
    platechars = "".join(re.findall("[a-zA-Z0-9]", plate))

    if len(platechars) == 7:
      return platechars, True
    else:
      return "", False


  def ocrPlateImage(self, image):
    config = r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 --psm 6 --oem 3'
    output = ""

    try:
      output = pytesseract.image_to_string(image, lang='estacionaqui', config=config)
    except:
      print("falha ao ler imagem com o tesseract")
      return "", False
    else:
      checkedPlate, isPlate = self.checkPlateChars(output)
      print("achou: " + output)
      return checkedPlate, isPlate


  def findLicensePlate(self, contours):
    img = cv2.imread(self.imageSource)
    foundPlateChars = []

    for c in contours:
      perimeter = cv2.arcLength(c, True)
      approx = cv2.approxPolyDP(c, 0.025 * perimeter, True)
      (x, y, alt, lar) = cv2.boundingRect(c)

      if len(approx) >= 4 and len(approx) <= 6:
        (x, y, alt, lar) = cv2.boundingRect(c)
        cv2.rectangle(img, (x, y), (x + alt, y + lar), (255, 0, 0), 2)
        roi = img[y:y + lar, x:x + alt]

        processedImage = self.preProcessPlateImage(roi)

        plateChars, foundPlate = self.ocrPlateImage(processedImage)

        if (foundPlate):
          foundPlateChars.append(plateChars)

    # cv2.imshow("contours", img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return foundPlateChars


  def cleanFiles(self):
    if Path(self.imageSource).is_file():
      os.remove(self.imageSource)


  def exec(self, imgSource, spotNum):
    foundPlate = []

    try:
      self.imageSource = imgSource
      self.spot_number = spotNum

      contours = self.findPossiblePlatesContours()
      foundPlate = self.findLicensePlate(contours)
    except Exception as e:
      print("falha no processo de leitura: " + str(e))

    # self.cleanFiles()

    return foundPlate[0] if len(foundPlate) > 0 else ""
