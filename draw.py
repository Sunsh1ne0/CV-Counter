import cv2

def enter_end_zones(cv_image, enter_zone_part, end_zone_part, horizontal=False):
        width = cv_image.shape[1]
        height = cv_image.shape[0]
        if horizontal:
            cv_image = cv2.line(cv_image, (0, int(height*enter_zone_part)), (width, int(height*enter_zone_part)), (0,0,255), 1)
            cv_image = cv2.line(cv_image, (0, int(height*end_zone_part)), (width, int(height*end_zone_part)), (0,0,255), 1)
        else:
            cv_image = cv2.line(cv_image, (int(width*enter_zone_part),0), (int(width*enter_zone_part),height), (0,0,255), 1)
            cv_image = cv2.line(cv_image, (int(width*end_zone_part), 0), (int(width*end_zone_part), height), (0,0,255), 1)
        return cv_image

def count(cv_image, count):
    return cv2.putText(cv_image, f"{count}", (30,30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 
                       2, cv2.LINE_AA)

def tracks(cv_image, tracks): 
    for key,values in tracks.items(): 
        color = (0, 0, 255)
        position = values[0][-1]
        status = values[1]
        if (status):
            color = (0, 255, 0)
        cv_image = cv2.circle(cv_image, (int(position[0]), int(position[1])), 0, color, 3) 
    return cv_image