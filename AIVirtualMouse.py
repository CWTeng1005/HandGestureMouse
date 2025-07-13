import cv2
import numpy as np
import HandTrackingModule as htm
import time
import autopy
import pyautogui

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
right_click_time = time.time()
left_click_time = time.time()
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
        # 3. Check which fingers are up
        fingers = detector.fingersUp()
        # print(fingers)
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (200, 0, 200), 2)

        # 右键：食指 + 中指
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            cv2.putText(img, f"Mode: MOUSE - Right Click", (400, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)
            index_middle_len, img, lineInfo = detector.findDistance(8, 12, img)
            if index_middle_len < 25:
                if time.time() - right_click_time > 0.8:
                    autopy.mouse.click(button=autopy.mouse.Button.RIGHT)
                    right_click_time = time.time()
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 12, (150, 0, 150), cv2.FILLED)

        # 左键：拇指 + 食指
        if fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            cv2.putText(img, f"Mode: MOUSE - Left Click", (400, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)
            d2, img, lineInfo = detector.findDistance(8, 12, img)
            if d2 < 30:
                if time.time() - left_click_time > 0.8:
                    autopy.mouse.click()    # 默认左键
                    left_click_time = time.time()
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 12, (150, 0, 150), cv2.FILLED)

        # 滚动：小拇指向上或向下
        if fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 1:
            cv2.putText(img, f"Mode: MOUSE - Scroll", (400, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)
            pinky_y = lmList[20][2]
            upper_threshold = 160   # 举得比较高（往上滚）
            lower_threshold = 320   # 放得比较低（往下滚）
            scroll_speed = 100   # 可调节滚动速度
            if pinky_y < upper_threshold:
                pyautogui.scroll(scroll_speed)  # 往上滚
                cv2.putText(img, f"SCROLL UP", (400, 70), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 0), 2)
            elif pinky_y > lower_threshold:
                pyautogui.scroll(-scroll_speed) # 往下滚
                cv2.putText(img, f"SCROLL DOWN", (400, 70), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 0), 2)

        # 鼠标移动：食指
        if fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            cv2.putText(img, f"Mode: MOUSE - Moving", (400, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)
            x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
            y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))
            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening
            clocX = np.clip(clocX, 0, wScr - 1)
            clocY = np.clip(clocY, 0, hScr - 1)
            autopy.mouse.move(clocX, clocY)
            cv2.circle(img, (x1, y1), 12, (125, 0, 125), cv2.FILLED)
            plocX, plocY = clocX, clocY

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

    # Frame Rate
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 30), cv2.FONT_HERSHEY_COMPLEX,
                0.5, (0, 0, 255), 2)
    cv2.putText(img, f"Mode: MOUSE", (400, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 0, 0), 2)

    # Display
    cv2.imshow("Frame", img)

    # press 'Q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break