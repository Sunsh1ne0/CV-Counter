import cv2
import numpy as np

class Draw:
    def __init__(self, resolution, enter_zone_part, end_zone_part, horizontal=False) -> None:
          self.scale = resolution[0]//320
          self.scale = self.scale if self.scale >= 1 else 1
          self.enter_zone_part = enter_zone_part
          self.end_zone_part = end_zone_part
          self.horizontal = horizontal

    def lines(self, cv_image):
        width = cv_image.shape[1]
        height = cv_image.shape[0]
        if self.horizontal:
            cv_image = cv2.line(cv_image, (0, int(height*self.enter_zone_part)), (width, int(height*self.enter_zone_part)), (0,0,255), self.scale)
            cv_image = cv2.line(cv_image, (0, int(height*self.end_zone_part)), (width, int(height*self.end_zone_part)), (0,0,255), self.scale)
        else:
            cv_image = cv2.line(cv_image, (int(width*self.enter_zone_part),0), (int(width*self.enter_zone_part),height), (0,0,255), self.scale)
            cv_image = cv2.line(cv_image, (int(width*self.nd_zone_part), 0), (int(width*self.end_zone_part), height), (0,0,255), self.scale)
        return cv_image
    
    def count(self, cv_image, count):
        return cv2.putText(cv_image, f"{count}", (30,30 * self.scale), 
                       cv2.FONT_HERSHEY_SIMPLEX, self.scale, (0, 0, 255), 
                       self.scale+1, cv2.LINE_AA)
    
    def tracks(self, cv_image, eggs): 
        for _,egg in eggs.items(): 
            color = (0, 255, 0) if (egg.counted) else (0, 0, 255)
            position = (int(egg.position[0]), int(egg.position[1]))
            cv_image = cv2.circle(cv_image, position, self.scale, color, self.scale+2) 
        return cv_image
    
    def boxes(self,cv_image, results):
        _boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)
        color = (0,0,255)
        for box in _boxes:
            x1, y1, x2, y2 = box
            cv2.rectangle(cv_image, (x1, y1), (x2, y2), color, self.scale + 1)
        return cv_image
    
    def process(self, cv_image, eggs, count, results, tracks_f:bool = True, lines_f:bool = True, count_f:bool = True, boxes_f:bool = False):
        _image = cv_image.copy()
        if tracks_f:
            _image = self.tracks(_image, eggs)
        if lines_f:
            _image = self.lines(_image)
        if count_f:
            _image = self.count(_image, count)
        if boxes_f:
            _image = self.boxes(_image, results)
        return _image

