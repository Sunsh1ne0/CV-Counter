from collections import defaultdict  

class Egg():
    def __init__(self) -> None:
        self.position = (0,0)
        self.counted  = False
        self.lost_frames = 0
        self.right = False
        self.left = False
        self.right_frame = 0
        self.left_frame = 0
        pass


class Counter():
    def __init__(self, enter_zone_part, end_zone_part, horizontal, height, width):
        self.enter_zone_part = enter_zone_part
        self.end_zone_part = end_zone_part
        self.eggs = defaultdict(lambda: Egg())
        self.horizontal = horizontal
        self.height = height
        self.width = width
    
    def check_states(self, egg, frame_number):
        if self.horizontal:
            index = 1
            criteria = self.height
        else:
            index = 0
            criteria = self.width
        pass

        if (egg.position[index] < int(criteria * self.enter_zone_part)):
                egg.left = True
                egg.left_frame = frame_number
        if (egg.position[index] > int(criteria * self.end_zone_part)):
                egg.right = True
                egg.right_frame = frame_number
        
        if (egg.left and egg.right and egg.left_frame < egg.right_frame):
            egg.counted = True
            return True
        return False

    def is_track_actual(self, track):
        if (len(track) < 2):
                return False
        return True

    def last_new(self):
        states = []
        pos = []
        for _,egg in self.eggs.items():
            states.append(egg.counted)
            pos.append(egg.position)
        return states,pos

    def update(self, results, frame_number):
        dcount = 0
        if(results[0].boxes.id != None):
            boxes = results[0].boxes.xywh.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            for box, track_id in zip(boxes, track_ids):
                x, y, _, _ = box
                egg = self.eggs[track_id]
                egg.position = (float(x),float(y))
                if egg.counted == False:
                    if self.check_states(egg, frame_number):
                        dcount += 1
        else:
            track_ids = []
        
        ## clear lost
        keys = list(self.eggs.keys())
        for key in keys:
            if not key in track_ids:
                if( self.eggs[key].lost_frames < 30):
                    self.eggs[key].lost_frames += 1
                else:
                    del self.eggs[key]
        return dcount