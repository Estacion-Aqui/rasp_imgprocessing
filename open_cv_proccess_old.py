import cv2, os, pytesseract
from pathlib import Path
import numpy as np



class OpenCvProcess:

  imageSource = ""
  
  def preProccessImage(self, image):
    
    imgBlurred = cv2.GaussianBlur(image, (7, 7), 0)

    grey = cv2.cvtColor(imgBlurred, cv2.COLOR_BGR2GRAY)
    
    sobelx = cv2.Sobel(grey, cv2.CV_8U, 1, 0, ksize = 3)
    
    _, threshold_img = cv2.threshold(sobelx, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    element = cv2.getStructuringElement(shape = cv2.MORPH_RECT, ksize =(22, 3))
    morph_n_thresholded_img = threshold_img.copy()
    
    cv2.morphologyEx(src = threshold_img,
      op = cv2.MORPH_CLOSE,
      kernel = element,
      dst = morph_n_thresholded_img)
    
    cv2.imshow("threshold", threshold_img)
    cv2.waitKey(0)

    cv2.imshow("m_threshold", morph_n_thresholded_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
		
    return morph_n_thresholded_img
  
  def preRatioCheck(self, area, width, height):

    ratioMin = 2.5
    ratioMax = 7

    ratio = float(width) / float(height)
		
    if ratio < 1:
      ratio = 1 / ratio

    if (ratio < ratioMin or ratio > ratioMax):
      return False
		
    return True
  
  def validateRatio(self, rect):
    (x, y), (width, height), rect_angle = rect

    if (width > height):
    	angle = -rect_angle
    else:
    	angle = 90 + rect_angle

    if angle > 15:
    	return False
		
    if (height == 0 or width == 0):
    	return False

    area = width * height
		
    if not self.preRatioCheck(area, width, height):
    	return False
    else:
    	return True
   
  def ratioCheck(self, area, width, height):
		
    min = self.min_area
    max = self.max_area

    ratioMin = 3
    ratioMax = 6

    ratio = float(width) / float(height)
		
    if ratio < 1:
      ratio = 1 / ratio
		
    if (area < min or area > max) or (ratio < ratioMin or ratio > ratioMax):
      return False
		
    return True
   
  def clean_plate(self, plate):
		
    gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    cv2.imshow("treated_image", thresh)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
		
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if contours:
      areas = [cv2.contourArea(c) for c in contours]
			
			# index of the largest contour in the area
			# array
      max_index = np.argmax(areas)

      max_cnt = contours[max_index]
      max_cntArea = areas[max_index]
      x, y, w, h = cv2.boundingRect(max_cnt)
      rect = cv2.minAreaRect(max_cnt)
			
      if not self.ratioCheck(max_cntArea, plate.shape[1], plate.shape[0]):
        return plate, False, None
			
      return plate, True, [x, y, w, h]
		
    else:
      return plate, False, None
  
  def checkPlate(self, image, contour):
    
    min_rect = cv2.minAreaRect(contour)
    
    if self.validateRatio(min_rect):
      x, y, w, h = cv2.boundingRect(contour)
      after_validation_img = image[y:y + h, x:x + w]
      cv2.imshow("validated_image", after_validation_img)
      cv2.waitKey(0)
      cv2.destroyAllWindows()
      after_clean_plate_img, plateFound, coordinates = self.clean_plate(after_validation_img)

      print(coordinates)
      cv2.imshow("found_plate", plateFound)
      cv2.waitKey(0)
      cv2.destroyAllWindows()
      
      if plateFound:
          x1, y1, w1, h1 = coordinates
          coordinates = x1 + x, y1 + y
          
          return after_clean_plate_img, coordinates
    
    return None, None
    

  def findLicensePlate(self):
    
    inputImage = cv2.imread(self.imageSource)
    plates = []
    self.corresponding_area = []
    
    processedImage = self.preProccessImage(inputImage)

    contours, _ = cv2.findContours(processedImage, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    for cnt in contours:
      plateImage, coordinates = self.checkPlate(inputImage, cnt)
      
      if plateImage is not None:
        plates.append(plateImage)
        self.corresponding_area.append(coordinates)
        cv2.imshow("roi", plateImage)
        cv2.waitKey(0)
        cv2.imwrite('out/roi.png', plateImage)
        
    if (len(plates) > 0):
      return plates
    
    else:
      return None
    

  def preProcessPlateImage(self):
    img_roi = cv2.imread("out/roi.png")

    if img_roi is None:
      return

    resize_img_roi = cv2.resize(img_roi, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    img_grey = cv2.cvtColor(resize_img_roi, cv2.COLOR_BGR2GRAY)
    _, img_binary = cv2.threshold(img_grey, 70, 255, cv2.THRESH_BINARY)
    blurred_img = cv2.GaussianBlur(img_binary, (5, 5), 0)

    cv2.imwrite("out/roi-ocr.png", blurred_img)

    return blurred_img


  def ocrPlateImage(self):
    image = cv2.imread("out/roi-ocr.png")
    config = r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- --psm 6'
    output = ""

    # output = pytesseract.image_to_string(image, lang='mercosul', config=config)

    # return output

    try:
      output = pytesseract.image_to_string(image, lang='eng', config=config)
    except:
      print("falha ao ler imagem com o tesseract")
    else:
      print(output)
      return output

  def cleanFiles(self):
    if Path("out/roi.png").is_file():
      os.remove("out/roi.png")
    if Path("out/roi-ocr.png").is_file():
      os.remove("out/roi-ocr.png")
    if Path(self.imageSource).is_file():
      print(self.imageSource + " exists")
      os.remove(self.imageSource)


  def exec(self, imgSource):
    self.imageSource = imgSource

    plates = self.findLicensePlate()
    self.preProcessPlateImage()
    plateChars = self.ocrPlateImage()

  #  self.cleanFiles()

    return plateChars
