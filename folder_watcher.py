from img_processor import ImageProcessor
import os, time

class FolderWatcher:

  path_to_watch = "resources/"
  processor = ImageProcessor()

  def exec(self):

    beforeState = dict ([(file, None) for file in os.listdir (self.path_to_watch)])

    while 1:
      afterState = dict ([(file, None) for file in os.listdir (self.path_to_watch)])
      addedFiles = [file for file in afterState if not file in beforeState]

      if addedFiles:
        print("Added: ", ", ".join(addedFiles))
        for fileStr in addedFiles:
          fileExt = fileStr.split('.')[-1]
          if(fileExt == "jpg" or fileExt == "png" or fileExt == "jpeg"):
            time.sleep(1)
            self.processor.exec(self.path_to_watch + fileStr)
        break
      else:
        beforeState = afterState
