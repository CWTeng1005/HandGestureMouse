import cv2
import time
import math
import numpy as np
import HandTrackingModule as htm
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

wCam, hCam = 640, 480

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

detector = htm.handDetector(maxHands=1, detectionCon=0.7)

devices = AudioUtilities.GetSpeakers()
interface =  devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()
print(volRange)
minVol = -25
maxVol = volRange[1]
vol = 0
volBar = 400
volPer = 0
min_vol_range = 20
max_vol_range = 100

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)
    volume.SetMasterVolumeLevelScalar(0, None)  # 安全默认值
    if len(lmList) != 0:
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        cv2.circle(img, (x1, y1), 15, (255, 0, 0), cv2.FILLED)
        cv2.circle(img, (x2, y2), 15, (255, 0, 0), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 3)
        cv2.circle(img, (cx, cy), 15, (255, 0, 0), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)

        volPer = np.interp(length, [min_vol_range, max_vol_range], [0, 100]) # 画面音量
        volScalar = np.interp(length, [min_vol_range, max_vol_range], [0.0, 1.0]) # 实际系统音量
        volScalar = np.clip(volScalar, 0.0, 1.0) # 防止过界
        volume.SetMasterVolumeLevelScalar(volScalar, None)
        volBar = np.interp(length, [min_vol_range, max_vol_range], [400, 150])
        print(int(length), f"Volume %: {int(volPer)}")

        if length < 50:
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

    cv2.rectangle(img, (50, 147), (60, 403), (0, 0 ,0), 3)
    cv2.rectangle(img, (53, int(volBar)), (57, 400), (255, 255 ,255), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 255, 255), 3)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                1, (0, 0, 255), 2)

    cv2.imshow("Frame", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break