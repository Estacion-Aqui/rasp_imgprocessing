from helix_publisher import HelixPublisher

class ImageProcessor:

    def exec(self):
        id = 'urn:ngsi-ld:ParkingSpot:sbc:golden:001'
        attribute = { "current_plate" : { "value" : "AAA-4E01", "type" : "string" } }

        self.publish_to_helix(id, attribute)

    def publish_to_helix(self, id, attribute):
        publisher = HelixPublisher()
        
        publisher.send_message(id, attribute)