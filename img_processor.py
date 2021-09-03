from helix_publisher import HelixPublisher
from openCvProccess import OpenCvProcess

class ImageProcessor:

    def exec(self, imageSource):
        id = 'urn:ngsi-ld:ParkingSpot:sbc:golden:001'
        openCvProcessor = OpenCvProcess()
        attribute = {}
        plateChars = str(openCvProcessor.exec(imageSource)).rstrip().lstrip()

        if (len(plateChars) == 7):
            attribute = {
                "current_plate" : { "value" : str(plateChars), "type" : "string" },
                "status" : { "value" : "filled", "type" : "string" }
            }
        else:
            attribute = {
                "current_plate" : { "value" : "", "type" : "string" },
                "status" : { "value" : "free", "type" : "string" }
            }

        self.publish_to_helix(id, attribute)

    def publish_to_helix(self, id, attribute):
        publisher = HelixPublisher()

        publisher.send_message(id, attribute)