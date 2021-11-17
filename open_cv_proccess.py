import cv2, os, pytesseract, datetime, time
from pathlib import Path
import imutils
import numpy as np
import re
import matplotlib.pyplot as plt

class OpenCvProcess:

  pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"

  imageSource = ""

  spot_number = ""

  def findPossiblePlatesContours(self):
    img = cv2.imread(self.imageSource)
    element = cv2.getStructuringElement(cv2.MORPH_RECT, (22, 3))

    # cv2.imshow("original", img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

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

    kernel = np.ones((1, 1), np.uint8)

    resize_img_roi = cv2.resize(img_roi, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
    img_grey = cv2.cvtColor(resize_img_roi, cv2.COLOR_BGR2GRAY)

    img_dilated = cv2.dilate(img_grey, kernel, iterations=1)
    img_erode = cv2.erode(img_dilated, kernel, iterations=1)

    blurred_img = cv2.GaussianBlur(img_erode, (5, 5), 0)
    _, img_binary = cv2.threshold(blurred_img, 70, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    cv2.imshow("processed", img_binary)
    cv2.waitKey(1500)
    cv2.destroyAllWindows()

    return img_binary


  def checkPlateChars(self, plate):
    platechars = "".join(re.findall("[a-zA-Z0-9]", plate))

    if len(platechars) >= 7:
      return platechars[0:7], True
    else:
      return "", False


  def ocrPlateImage(self, image):
    config = r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 --psm 7 --oem 2'
    output = ""

    # cv2.imshow("ocr", image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    try:
      output = pytesseract.image_to_string(image, lang='eng', config=config)
    except Exception as e:
      print("falha ao ler imagem com o tesseract: " + str(e))
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
      (x, y, lar, alt) = cv2.boundingRect(c)

      if len(approx) >= 4 and len(approx) <= 6:
        (x, y, lar, alt) = cv2.boundingRect(c)
        cv2.rectangle(img, (x, y), (x + lar, y + alt), (255, 0, 0), 2)
        roi = img[y:y + alt, x:x + lar]
        # roi = img[y - 5:y + alt + 5, x - 5:x + lar + 5]

        try:
          processedImage = self.preProcessPlateImage(roi)
        except Exception as e:
          print("falha ao processar imagem: " + str(e))
          continue

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

    self.cleanFiles()

    return foundPlate[0] if len(foundPlate) > 0 else ""
