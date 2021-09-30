import cv2, os, pytesseract
from pathlib import Path



class OpenCvProcess:

  imageSource = ""

  def findLicensePlate(self):
    img = cv2.imread(self.imageSource)
    print(self.imageSource)

    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imshow("grey", img)
    cv2.waitKey(0)

    _, bin = cv2.threshold(grey, 90, 255, cv2.THRESH_BINARY)
    cv2.imshow("binary", img)
    cv2.waitKey(0)

    blurred = cv2.GaussianBlur(bin, (5, 5), 0)
    cv2.imshow("blurred", blurred)
    cv2.waitKey(0)

    contours, hierarchy = cv2.findContours(blurred, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    for c in contours:
      perimeter = cv2.arcLength(c, True)
      if perimeter > 120:
        approx = cv2.approxPolyDP(c, 0.03 * perimeter, True)
        if len(approx) == 4:
          (x, y, alt, lar) = cv2.boundingRect(c)
          cv2.rectangle(img, (x, y), (x + alt, y + lar), (0, 255, 0), 2)
          roi = img[y:y + lar, x:x + alt]
          cv2.imwrite('out/roi.png', roi)

    cv2.imshow("contours", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


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
    config = r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 --psm 6'
    output = ""

    try:
      output = pytesseract.image_to_string(image, lang='eng', config=config)
    except:
      print("falha ao ler imagem com o tesseract")
    else:
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

    self.findLicensePlate()
    self.preProcessPlateImage()
    plateChars = self.ocrPlateImage()

  #  self.cleanFiles()

    return plateChars
