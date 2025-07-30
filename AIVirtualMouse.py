import cv2
import numpy as np
import HandTrackingModule as htm
import time
import autopy
import pyautogui
import threading
import tkinter as tk
import os
import subprocess
import psutil

##################################
wCam, hCam = 640, 480
frameR = 120 # frame reduction
smoothening = 4
warning_active = False
##################################

pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0
warning_image = np.zeros((100, 400, 3), dtype=np.uint8)
cap = cv2.VideoCapture(1)
cap.set(3, wCam)
cap.set(4, hCam)
detector = htm.handDetector(maxHands=1)
wScr, hScr = autopy.screen.size()
right_click_time = time.time()
left_click_time = time.time()
# print(wScr, hScr)
# 1920, 1080

################################## 虚拟键盘 ##################################

# 屏幕按钮窗口
def create_launcher():
    root = tk.Tk()
    root.title("Launcher")
    root.geometry("160x120+100+100")
    root.attributes("-topmost", True)

    def toggle_system_keyboard():
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'TabTip.exe':
                os.system('taskkill /IM TabTip.exe /F')
                return
        subprocess.Popen(["explorer.exe", r"C:\Program Files\Common Files\Microsoft Shared\ink\TabTip.exe"])

    def run_pluck_string():
        import pluck_string
        pluck_string.run_game()
        print("Pluck String Launched.")

    def run_sand_flow():
        # import sand_flow.run()
        print("Sand Flow Launched.")

    def open_destress_menu():
        menu = tk.Toplevel(root)
        menu.title("De-Stress Games")
        menu.geometry("200x150+200+200")
        menu.attributes("-topmost", True)
        tk.Button(menu, text="Pluck String", width=15, command=run_pluck_string).pack(pady=5)
        tk.Button(menu, text="Sand Flow", width=15, command=run_sand_flow).pack(pady=5)

    tk.Button(root, text="Keyboard", height=1, width=10, command=toggle_system_keyboard).pack(pady=5, fill=tk.X)
    tk.Button(root, text="De-Stress", height=1, width=10, command=open_destress_menu).pack(pady=5, fill=tk.X)

    root.mainloop()

# 用线程启动 GUI
threading.Thread(target=create_launcher, daemon=True).start()

################################## 虚拟键盘 ##################################

################################## 虚拟鼠标 ##################################
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

        # 左键双击：食指 + 中指 + 无名指靠近（无拇指）
        if fingers == [0, 1, 1, 1, 0]:
            d1, img, _ = detector.findDistance(8, 12, img)  # 食指-中指
            d2, img, _ = detector.findDistance(12, 16, img)  # 中指-无名指
            cv2.putText(img, "Double Click", (400, 70), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)
            if d1 < 25 and d2 < 25 and time.time() - left_click_time > 1.2:
                autopy.mouse.click()
                autopy.mouse.click()
                left_click_time = time.time()

        # 滚动：小拇指向上或向下
        if fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 1:
            cv2.putText(img, f"Mode: MOUSE - Scroll", (400, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)
            pinky_x, pinky_y = lmList[20][1:]
            upper_threshold = 160   # 举得比较高（往上滚）
            lower_threshold = 300   # 放得比较低（往下滚）
            scroll_speed = 100   # 可调节滚动速度
            cv2.circle(img, (pinky_x, pinky_y), 12, (125, 0, 125), cv2.FILLED)
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
        margin = 50
        ref_x, ref_y = None, None
        if fingers == [0, 1, 0, 0, 0]:  # 移动用食指
            ref_x, ref_y = lmList[8][1:]
        elif fingers == [0, 0, 0, 0, 1]:  # 滚动用小拇指
            ref_x, ref_y = lmList[20][1:]
        elif fingers == [0, 1, 1, 0, 0]:  # 右键
            ref_x, ref_y = lmList[12][1:]
        elif fingers == [1, 1, 0, 0, 0]:  # 左键
            ref_x, ref_y = lmList[4][1:]
        elif fingers == [0, 1, 1, 1, 0]:  # 左键双击
            ref_x, ref_y = lmList[12][1:]

        if ref_x is not None:
            out_of_bounds = (
                    ref_x < frameR - margin or ref_x > wCam - frameR + margin or
                    ref_y < frameR - margin or ref_y > hCam - frameR + margin
            )
            if out_of_bounds and not warning_active:
                warning_image[:] = 0
                cv2.putText(warning_image, "Out of control zone!", (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.imshow("Warning", warning_image)
                warning_active = True
            elif not out_of_bounds and warning_active:
                cv2.destroyWindow("Warning")
                warning_active = False

    ################################## 虚拟鼠标 ##################################

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