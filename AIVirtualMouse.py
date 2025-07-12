import cv2
import numpy as np
import HandTrackingModule as htm
import time
import autopy

##################################
wCam, hCam = 640, 480
frameR = 100 # frame reduction
smoothening = 5
warning_active = False
##################################

pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0
warning_image = np.zeros((100, 400, 3), dtype=np.uint8)
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
detector = htm.handDetector(maxHands=1)
wScr, hScr = autopy.screen.size()
# print(wScr, hScr)
# 1920, 1080

while True:
    # 1. Find landmarks
    success, img = cap.read()
    img = detector.findHands(img)
    lmList, bbox = detector.findPositionBox(img)

    # 2. Get the tip of the index and middle fingers
    if len(lmList) != 0:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]
        # print(x1, y1, x2, y2)

        # 3. Check which fingers are up
        fingers = detector.fingersUp()
        # print(fingers)

        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (200, 0, 200), 2)
        # 4. Only Index Finger: Moving Mode
        if fingers[1] == 1 and fingers[2] == 0 and fingers[0] == 0 and fingers[3] == 0 and fingers[4] == 0:

            # 5. Convert Coordinates
            x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
            y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))

            # 6. Smoothen Values
            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening
            clocX = np.clip(clocX, 0, wScr - 1)
            clocY = np.clip(clocY, 0, hScr - 1)
            # 7. Move Mouse
            autopy.mouse.move(clocX, clocY)
            # autopy.mouse.move(wScr - clocX, clocY)
            cv2.circle(img, (x1, y1), 12, (125, 0, 125), cv2.FILLED)
            plocX, plocY = clocX, clocY

        # 8. Both Index and Middle fingers are up: Clicking Mode
        # 判断是否举起食指和中指（右键）或食指和拇指（左键）
        if fingers[1] == 1 and fingers[2] == 1:
            # 9. Find distance between fingers
            index_middle_len, img, lineInfo = detector.findDistance(8, 12, img)
            # print(index_middle_len)
            # 10. Click mouse if distance short
            if index_middle_len < 25:
                autopy.mouse.click(button=autopy.mouse.Button.RIGHT)
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 12, (150, 0, 150), cv2.FILLED)

        if fingers[1] == 1 and fingers[0] == 1:
            # 拇指 + 食指：左键
            thumb_index_len, img, lineInfo = detector.findDistance(4, 8, img)
            if thumb_index_len < 30:
                autopy.mouse.click()    # 默认左键
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 12, (150, 0, 150), cv2.FILLED)

        # 出界监测
        out_of_bounds = x1 < frameR or x1 > wCam - frameR or y1 < frameR or y1 > hCam - frameR
        if out_of_bounds and not warning_active:
            warning_image[:] = 0 # 清空背景
            cv2.putText(warning_image, "Out of control zone!", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.imshow("Warning", warning_image)
            warning_active = True
        elif not out_of_bounds and warning_active:
            cv2.destroyWindow("Warning")
            warning_active = False

    # 11. Frame Rate
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                0.5, (0, 0, 255), 2)
    cv2.putText(img, f"Mode: MOUSE", (450, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 2)

    # 12. Display
    cv2.imshow("Frame", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break