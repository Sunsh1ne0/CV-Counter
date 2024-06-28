import cv2

def enter_end_zones(cv_image, enter_zone_part, end_zone_part, horizontal=False):
        width = cv_image.shape[1]
        height = cv_image.shape[0]
        if horizontal:
            cv_image = cv2.line(cv_image, (0, int(height*enter_zone_part)), (width, int(height*enter_zone_part)), (0,0,255), 2)
            cv_image = cv2.line(cv_image, (0, int(height*end_zone_part)), (width, int(height*end_zone_part)), (0,0,255), 2)
        else:
            cv_image = cv2.line(cv_image, (int(width*enter_zone_part),0), (int(width*enter_zone_part),height), (0,0,255), 2)
            cv_image = cv2.line(cv_image, (int(width*end_zone_part), 0), (int(width*end_zone_part), height), (0,0,255), 2)
        return cv_image

def count(cv_image, count):
    return cv2.putText(cv_image, f"{count}", (30,80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 
                       2, cv2.LINE_AA)

def tracks(cv_image, eggs): 
    _image = cv_image.copy()
    for _,egg in eggs.items(): 
        color = (0, 0, 255)
        if (egg.counted):
            color = (0, 255, 0)
        position = (int(egg.position[0]), int(egg.position[1]))
        _image = cv2.circle(_image, position, 5, color, 7) 
    return _image