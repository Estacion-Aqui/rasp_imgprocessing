from helix_publisher import HelixPublisher
from open_cv_proccess import OpenCvProcess
import cv2

class ImageProcessor:

    def exec(self, imageSource):
        id = 'urn:ngsi-ld:ParkingSpot:' + self.getSpotId(imageSource)
        openCvProcessor = OpenCvProcess()
        attribute = {}
        # plateChars = str(openCvProcessor.exec(imageSource)).rstrip().lstrip()
        img = cv2.imread(imageSource)

        plateChars = openCvProcessor.find_possible_plates(img)

        print(plateChars)

        if plateChars is not None:
                 
                for i, p in enumerate(possible_plates):
                    chars_on_plate = findPlate.char_on_plate[i]
 
                    cv2.imshow('plate', p)
                    cv2.waitKey(0)

        # if (len(plateChars) > 6 and len(plateChars) < 9):
        #     attribute = {
        #         "current_plate" : { "value" : str(plateChars), "type" : "string" },
        #         "status" : { "value" : "filled", "type" : "string" }
        #     }
        # else:
        #     attribute = {
        #         "current_plate" : { "value" : "", "type" : "string" },
        #         "status" : { "value" : "free", "type" : "string" }
        #     }

        # print(attribute)
        # print(id)
        # self.publish_to_helix(id, attribute)


    def getSpotId(self, imageSource):
        filename = imageSource.split("/")[-1]
        id = filename.split("_")[0]

        return str(id).replace("-", ":")


    def publish_to_helix(self, id, attribute):
        publisher = HelixPublisher()

        publisher.send_message(id, attribute)