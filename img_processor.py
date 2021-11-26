from helix_publisher import HelixPublisher
from open_cv_proccess import OpenCvProcess


class ImageProcessor:

    def exec(self, imageSource):
        openCvProcessor = OpenCvProcess()

        cam_id, spot_status = self.getSpotId(imageSource)
        id = 'urn:ngsi-ld:ParkingSpot:' + cam_id
        plateChars = str(openCvProcessor.exec(imageSource)).rstrip().lstrip()

        attribute = {
            "current_plate" : { "value" : plateChars, "type" : "string" },
            "status" : { "value" : spot_status, "type" : "string" }
        }

        self.publish_to_helix(id, attribute)


    def getSpotId(self, imageSource):
        filename = imageSource.split("/")[-1]
        id = filename.split("_")[0]
        spot_status = filename.split("_")[1]

        return str(id).replace("-", ":"), str(spot_status)


    def publish_to_helix(self, id, attribute):
        publisher = HelixPublisher()

        publisher.send_message(id, attribute)
