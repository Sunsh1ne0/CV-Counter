from collections import defaultdict  

class Counter():
    def __init__(self, enter_zone_part, end_zone_part, horizontal, height, width):
        self.enter_zone_part = enter_zone_part
        self.end_zone_part = end_zone_part
        self.track_history = defaultdict(lambda: [[], False, 0])
        self.horizontal = horizontal
        self.height = height
        self.width = width

    def is_track_pass_board(self, track):
        is_left_point_exist = 0
        is_right_point_exist = 0
        left_point_frame = 0
        right_point_frame = 0

        if self.horizontal:
            index = 1
            criteria = self.height
        else:
            index = 0
            criteria = self.width

        for i in range(len(track)):
            point = track[i]
            if (point[index] < int(criteria * self.enter_zone_part)):
                is_left_point_exist = 1
                left_point_frame = i
            if (point[index] > int(criteria * self.end_zone_part)):
                is_right_point_exist = 1
                right_point_frame = i

        if (is_left_point_exist * is_right_point_exist == 1 and
                left_point_frame < right_point_frame):
            return True
        return False

    def is_track_actual(self, track):
        if (len(track) < 2):
                return False
        return True

    def last(self):
        states = []
        pos = []
        for key,values in self.track_history.items():
            position = values[0][-1]
            status = values[1]
            states.append(status)
            pos.append(position)
        return states,pos


    def update(self, results):
        dcount = 0
        if(results[0].boxes.id != None):
            boxes = results[0].boxes.xywh.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            if self.horizontal:
                index = 1
                criteria = self.height
            else:
                index = 0
                criteria = self.width
            for box, track_id in zip(boxes, track_ids):
                x, y, w, h = box
                track_C = self.track_history[track_id]
                track = track_C[0]
                is_counted = track_C[1]
                track.append((float(x),float(y)))
                if track[-1][index] > criteria * self.end_zone_part and is_counted == False:
                    if self.is_track_pass_board(track):
                        dcount += 1
                        track_C[1] = True
        else:
            track_ids = []
        

        ## clear lost
        keys = list(self.track_history.keys())
        for key in keys:
            if not key in track_ids:
                if( self.track_history[key][2] < 30):
                    self.track_history[key][2] += 1
                else:
                    del self.track_history[key]
        return dcount