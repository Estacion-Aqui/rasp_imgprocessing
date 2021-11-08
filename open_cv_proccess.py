import cv2, os, pytesseract, datetime, time
from pathlib import Path
import imutils
import numpy as np
import re



class OpenCvProcess:

  #pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

  imageSource = ""

  spot_number = ""

  plate_file = "./readplates.txt"

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

    cv2.imshow("original", img)
    cv2.waitKey(0)

    # cv2.imshow("grey", grey)
    # cv2.waitKey(0)

    cv2.imshow("morph", morph_n_thresholded_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # cv2.imwrite("out/grey_"+ self.spot_number +"_"+ datetime.datetime.now().strftime("%H%M%S%d%m%Y") +".png", grey)
    # cv2.imwrite("out/threshold_"+ self.spot_number +"_"+ datetime.datetime.now().strftime("%H%M%S%d%m%Y") +".png", threshold_img)
    # cv2.imwrite("out/morph_"+ self.spot_number +"_"+ datetime.datetime.now().strftime("%H%M%S%d%m%Y") +".png", morph_n_thresholded_img)

    contours = cv2.findContours(morph_n_thresholded_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    contours = sorted(contours,key=cv2.contourArea, reverse = True)[:5]

    return contours


  def preProcessPlateImage(self, img_roi):
    if img_roi is None:
      return

    cv2.imshow("plate", img_roi)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

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
    config = r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 --psm 6'
    output = ""

    # output = pytesseract.image_to_string(image, lang='eng', config=config)
    # return output, False

    try:
      output = pytesseract.image_to_string(image, lang='eng', config=config)
    except:
      print("falha ao ler imagem com o tesseract")
      return "", False
    else:
      f = open(self.plate_file, "a")
      f.write(output)
      f.close()

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

        # cv2.imshow("processedImage", processedImage)
        # cv2.waitKey(1000)
        # cv2.destroyAllWindows()

        plateChars, foundPlate = self.ocrPlateImage(processedImage)

        if (foundPlate):
          foundPlateChars.append(plateChars)
          # cv2.imshow("roi", roi)
          # cv2.waitKey(6000)
          # cv2.destroyAllWindows()

    cv2.imshow("contours", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return foundPlateChars


  def cleanFiles(self):
    # if Path("out/roi.png").is_file():
    #   os.remove("out/roi.png")
    # if Path("out/roi-ocr.png").is_file():
    #   os.remove("out/roi-ocr.png")
    if Path(self.imageSource).is_file():
      os.remove(self.imageSource)


  def exec(self, imgSource, spotNum):
    foundPlate = []

    try:
      self.imageSource = imgSource
      self.spot_number = spotNum

      contours = self.findPossiblePlatesContours()
      foundPlate = self.findLicensePlate(contours)
    except:
      print("falha no processo de leitura")

    self.cleanFiles()

    f = open(self.plate_file, "a")
    f.write("\n-----------------------------------------------------------------------\n")
    f.close()

    return foundPlate[0] if len(foundPlate) > 0 else ""
