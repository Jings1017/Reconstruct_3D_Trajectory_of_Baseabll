if __name__ == "__main__":
    import cv2
    import argparse
    from os import makedirs
    from os.path import exists
    from pathlib import Path
    import numpy as np
    import cv2
    import glob
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="input video")
    parser.add_argument("--output", type=str, help="output frame folder")
    parser.add_argument(
        "--chessboard_size", nargs="+", type=int, help="chessboard_size"
    )
    args = parser.parse_args()

    chessboard_size = tuple(args.chessboard_size)
    input_folder = args.input
    output_path = args.output

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0 : chessboard_size[0], 0 : chessboard_size[1]].T.reshape(
        -1, 2
    )

    objpoints = []
    imgpoints = []
    images = glob.glob(input_folder + "/*.png")

    success_frame = []
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)
        print(ret)
        if ret == True:
            print("Reading: ", fname)
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)
            base = os.path.basename(fname)
            success_frame.append(os.path.splitext(base)[0])
            cv2.drawChessboardCorners(img, chessboard_size, corners2, ret)
            cv2.imshow("chess", img)
            cv2.waitKey(500)
            
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
                objpoints, imgpoints, gray.shape[::-1], None, None
            )
            np.savez(
                output_path,
                ret=ret,
                camera_matrix=mtx,
                dist_coefs=dist,
                rvecs=rvecs,
                tvecs=tvecs,
            )

    data = np.load(output_path)
    print('mtx: ',data['camera_matrix'])
    print('dist: ',data['dist_coefs'])
    cv2.destroyAllWindows()
    print(sorted(success_frame))
