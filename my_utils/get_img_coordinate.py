import cv2
import argparse

def draw_img(coordinate_list, img):
    circle_color = (0, 0, 255)
    img_draw = copy.deepcopy(img)
    for i, (x, y) in enumerate(coordinate_list):
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.circle(img_draw, (x, y), 1, circle_color, -1)

    cv2.imshow("check", img_draw)
    return img_draw

def click_event(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(x, " ", y)
        coordinate_list.append([x, y])
        draw_img(coordinate_list, img)

if __name__ == "__main__":
    from pathlib import Path
    import copy
    import numpy as np

    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, help="source video")
    parser.add_argument(
        "--output", type=str, default="coordinate.npy", help="<ref_point.npy>"
    )
    args = parser.parse_args()

    coordinate_list = []

    cap = cv2.VideoCapture(str(Path(args.video)))
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            cv2.imshow("frame", frame)
            key = cv2.waitKey(100)
            if key == ord("q") or key == 27:  # q or esc
                break
            elif key == 13:  # enter
                img = copy.deepcopy(frame)
                cv2.imshow("check", img)
                cv2.setMouseCallback("check", click_event)

                while True:
                    key = cv2.waitKey(0)
                    print(coordinate_list)
                    if key == ord("x") and len(coordinate_list) > 0:
                        coordinate_list.pop()
                        draw_img(coordinate_list, img)
                    elif key == ord("a") and len(coordinate_list) > 0:
                        coordinate = coordinate_list.pop()
                        coordinate_list.append([coordinate[0] - 1, coordinate[1]])
                        draw_img(coordinate_list, img)
                    elif key == ord("w") and len(coordinate_list) > 0:
                        coordinate = coordinate_list.pop()
                        coordinate_list.append([coordinate[0], coordinate[1] - 1])
                        draw_img(coordinate_list, img)
                    elif key == ord("d") and len(coordinate_list) > 0:
                        coordinate = coordinate_list.pop()
                        coordinate_list.append([coordinate[0] + 1, coordinate[1]])
                        draw_img(coordinate_list, img)
                    elif key == ord("s") and len(coordinate_list) > 0:
                        coordinate = coordinate_list.pop()
                        coordinate_list.append([coordinate[0], coordinate[1] + 1])
                        draw_img(coordinate_list, img)
                    elif key == 27:
                        break
                    elif key == ord("z"):
                        print("saving coordinate to " + str(Path(args.output)))
                        np.save(str(Path(args.output)), np.array(coordinate_list))
                        draw_img = draw_img(coordinate_list, img)
                        cv2.imwrite(str(Path(args.video)) + "_corrdinate.png", draw_img)
                        break
    cv2.destroyAllWindows()
