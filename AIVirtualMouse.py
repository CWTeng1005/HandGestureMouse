import cv2
import numpy as np
import time
import autopy
import pyautogui
import threading
import tkinter as tk
import os
import subprocess
import psutil

import HandTrackingModule as htm
from gesture_calculator import GestureCalculator
from left_digit_controller import LeftDigitRecognizer
import usage_guide

################################## ↓ 音量控制 ↓ ##################################
try:
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    _PYCAW_OK = True
except Exception:
    _PYCAW_OK = False

volume_mode = False
if _PYCAW_OK:
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        endpoint = cast(interface, POINTER(IAudioEndpointVolume))
    except Exception:
        _PYCAW_OK = False
################################## ↑ 音量控制 ↑ ##################################

##################################################################################
wCam, hCam = 640, 480
frameR = 120  # frame reduction
smoothening = 4
warning_active = False

pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0
warning_image = np.zeros((100, 400, 3), dtype=np.uint8)

# 新增：快速指南开关（H 键）
show_quick_guide = False

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

detector = htm.handDetector(maxHands=1)  # 保持回退版：右手鼠标用；左手数字由 LeftDigitRecognizer 自己跑
wScr, hScr = autopy.screen.size()
right_click_time = time.time()
left_click_time = time.time()
# print(wScr, hScr)  # 1920, 1080

# —— 计算器 & 左手数字识别 —— #
calc_mode = False
calc       = None
left_digit = LeftDigitRecognizer(
    stable_frames=8,
    rearm_frames=4,
    invert_handedness=False,   # 保持回退版
    debug=False
)

dragging = False
in_standby = False

min_vol_range = 20
max_vol_range = 120

##################################################################################

################################## ↓ UI Launcher ↓ ##################################
def create_launcher():
    root = tk.Tk()
    root.title("Launcher")
    root.geometry("400x400+1000+200")
    root.attributes("-topmost", True)

    def toggle_system_keyboard():
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'TabTip.exe':
                os.system('taskkill /IM TabTip.exe /F')
                return
        subprocess.Popen(["explorer.exe", r"C:\Program Files\Common Files\Microsoft Shared\ink\TabTip.exe"])

    # 后台线程启动游戏
    def run_asmr_mixer():
        def _run():
            try:
                import asmr_mixer
                asmr_mixer.run_game()
                print("ASMR Mixer Launched.")
            except Exception as e:
                print("ASMR Mixer error:", e)
        threading.Thread(target=_run, daemon=True).start()

    def run_sand_flow():
        print("Sand Flow Launched.")  # 占位

    # 音量按钮（保持原逻辑；先不改成左手）
    def toggle_volume_mode(event=None):
        global volume_mode
        volume_mode = not volume_mode
        print(f"[VolumeMode] -> {volume_mode}")
        vol_btn.config(text=f"Volume: {'ON' if volume_mode else 'OFF'}")

    # 打开计算器
    def open_calculator():
        global calc_mode, calc
        if calc is None:
            calc = GestureCalculator(master=root, topmost=True)
            def _on_calc_close():
                global calc_mode
                calc.hide()
                calc_mode = False
            try:
                calc.root.protocol("WM_DELETE_WINDOW", _on_calc_close)
            except Exception:
                pass
        else:
            calc.show()
        calc_mode = True

    # 打开详细用户指南（使用 usage_guide.py）
    def open_user_guide():
        try:
            usage_guide.open_detailed_guide(root)
        except Exception as e:
            print("open_detailed_guide error:", e)

    tk.Button(root, text="Keyboard (TabTip)", height=2, command=toggle_system_keyboard).pack(pady=5, fill=tk.X)
    tk.Button(root, text="ASMR Mixer",        height=2, command=run_asmr_mixer).pack(pady=5, fill=tk.X)
    tk.Button(root, text="Calculator (C)",    height=2, command=open_calculator).pack(pady=5, fill=tk.X)
    tk.Button(root, text="User Guide",        height=2, command=open_user_guide).pack(pady=5, fill=tk.X)
    vol_btn = tk.Button(root, text="Volume: OFF", height=2, command=toggle_volume_mode, state=("normal" if _PYCAW_OK else "disabled"))
    vol_btn.pack(pady=5, fill=tk.X)
    tk.Button(root, text="Exit (Q)",          height=2, command=lambda: os._exit(0)).pack(pady=5, fill=tk.X)

    # F9 切换音量开关（窗口有焦点时）
    root.bind("<F9>", toggle_volume_mode)

    # 保持置顶（每秒提升一次）
    def keep_topmost():
        try:
            root.lift()
            root.attributes("-topmost", True)
        finally:
            root.after(1000, keep_topmost)
    keep_topmost()

    root.mainloop()

# 用线程启动 GUI（非阻塞）
threading.Thread(target=create_launcher, daemon=True).start()
################################## ↑ UI Launcher ↑ ##################################

################################## ↓ 主循环：右手鼠标 + 左手数字 ↓ ##################################
while True:
    # 1) 取帧 & 可视化
    success, img = cap.read()
    if not success:
        break

    # HandTrackingModule 里已经水平镜像
    img = detector.findHands(img)
    lmList, bbox = detector.findPositionBox(img)

    # 2) 计算器开着时：仅用左手出“数字”，右手鼠标不受影响
    if calc_mode and calc is not None:
        digit = left_digit.update(img)  # 左手：握拳上膛 -> 出一位 -> 再握拳
        if digit is not None:
            calc.append_digit(digit)
            # 小提示：显示一下数字
            cv2.putText(img, f"Digit:{digit}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,165,255), 2)

    # 3) 右手鼠标逻辑（保持回退版）
    if len(lmList) != 0:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]

        fingers = detector.fingersUp()  # [thumb, index, middle, ring, pinky]
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (200, 0, 200), 2)

        # —— 音量控制（保持回退版的“右手拇指+食指”触发）——
        if volume_mode and _PYCAW_OK:
            if fingers == [1, 1, 0, 0, 0]:
                d, img, _ = detector.findDistance(4, 8, img)  # 拇指尖(4) - 食指尖(8)
                vol_scalar = np.interp(d, [min_vol_range, max_vol_range], [0.0, 1.0])
                vol_scalar = float(np.clip(vol_scalar, 0.0, 1.0))
                try:
                    endpoint.SetMasterVolumeLevelScalar(vol_scalar, None)
                except Exception:
                    pass

                # 画面提示
                vol_per = int(vol_scalar * 100)
                cv2.putText(img, "Mode: VOLUME", (400, 90), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 0), 2)
                cv2.rectangle(img, (50, 147), (60, 403), (0, 0, 0), 2)
                bar_y = int(np.interp(d, [min_vol_range, max_vol_range], [400, 150]))
                cv2.rectangle(img, (53, bar_y), (57, 400), (255, 255, 255), cv2.FILLED)
                cv2.putText(img, f'{vol_per} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                            1, (255, 255, 255), 2)

        # 拖拽逻辑（五指=待机；拳头=开始拖拽；回五指=释放）
        if fingers == [1, 1, 1, 1, 1]:  # 伸出五指，待机状态
            in_standby = True
            if dragging:
                pyautogui.mouseUp()  # 释放左键
                dragging = False
            cv2.putText(img, "Mode: MOUSE - Standby", (400, 80), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)

        elif fingers == [0, 0, 0, 0, 0] and in_standby and not dragging:
            pyautogui.mouseDown()   # 按下左键
            dragging = True
            in_standby = False  # 退出待机状态
            cv2.putText(img, "Mode: MOUSE - Dragging", (400, 80), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)

        if dragging:
            cv2.putText(img, "Mode: MOUSE - Dragging", (400, 80), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)

        # 右键：食指 + 中指
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            cv2.putText(img, "Mode: MOUSE - Right Click", (400, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)
            index_middle_len, img, lineInfo = detector.findDistance(8, 12, img)
            if index_middle_len < 25:
                if time.time() - right_click_time > 0.8:
                    autopy.mouse.click(button=autopy.mouse.Button.RIGHT)
                    right_click_time = time.time()
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 12, (150, 0, 150), cv2.FILLED)

        # 左键：拇指 + 食指
        if fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            cv2.putText(img, "Mode: MOUSE - Left Click", (400, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)
            d2, img, lineInfo = detector.findDistance(8, 12, img)
            if d2 < 30:
                if time.time() - left_click_time > 0.8:
                    autopy.mouse.click()    # 默认左键
                    left_click_time = time.time()
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 12, (150, 0, 150), cv2.FILLED)

        # 左键双击：食指 + 中指 + 无名指靠近（无拇指）
        if fingers == [0, 1, 1, 1, 0]:
            d1, img, _ = detector.findDistance(8, 12, img)   # 食指-中指
            d2, img, _ = detector.findDistance(12, 16, img)  # 中指-无名指
            cv2.putText(img, "Double Click", (400, 70), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)
            if d1 < 25 and d2 < 25 and time.time() - left_click_time > 1.2:
                autopy.mouse.click()
                autopy.mouse.click()
                left_click_time = time.time()

        # 滚动：小拇指向上或向下
        if fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 1:
            cv2.putText(img, "Mode: MOUSE - Scroll", (400, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 0), 2)
            pinky_x, pinky_y = lmList[20][1:]
            upper_threshold = 160   # 举得比较高（往上滚）
            lower_threshold = 300   # 放得比较低（往下滚）
            scroll_speed = 100      # 可调节滚动速度
            cv2.circle(img, (pinky_x, pinky_y), 12, (125, 0, 125), cv2.FILLED)
            if pinky_y < upper_threshold:
                pyautogui.scroll(scroll_speed)  # 往上滚
                cv2.putText(img, "SCROLL UP", (400, 70), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 0), 2)
            elif pinky_y > lower_threshold:
                pyautogui.scroll(-scroll_speed) # 往下滚
                cv2.putText(img, "SCROLL DOWN", (400, 70), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 0), 2)

        # 鼠标移动：食指
        if fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            cv2.putText(img, "Mode: MOUSE - Moving", (400, 50), cv2.FONT_HERSHEY_SIMPLEX,
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
        if fingers == [0, 1, 0, 0, 0]:        # 移动用食指
            ref_x, ref_y = lmList[8][1:]
        elif fingers == [0, 0, 0, 0, 1]:      # 滚动用小拇指
            ref_x, ref_y = lmList[20][1:]
        elif fingers == [0, 1, 1, 0, 0]:      # 右键
            ref_x, ref_y = lmList[12][1:]
        elif fingers == [0, 1, 1, 1, 0]:      # 左键双击
            ref_x, ref_y = lmList[12][1:]
        elif dragging:                        # 拖拽
            ref_x, ref_y = lmList[0][1:]

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

    # 4) 帧率 & 模式标签
    cTime = time.time()
    fps = 1 / (cTime - pTime) if cTime != pTime else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (18, 26), cv2.FONT_HERSHEY_COMPLEX,
                0.5, (0, 0, 255), 2)
    if calc_mode:
        cv2.putText(img, f"Mode: CALC (Left hand digits)", (360, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    else:
        cv2.putText(img, "Mode: MOUSE", (400, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

    # 快速指南（H 键）
    if show_quick_guide:
        try:
            usage_guide.draw_quick_guide(img, corner="tr", margin=(14, 46), alpha=0.88)
        except Exception as e:
            pass

    # 显示
    cv2.imshow("Frame", img)

    # 键盘控制
    key = cv2.waitKey(1) & 0xFF
    # 兼容你原先：按 v 关闭计算器
    if key == ord('v') and calc_mode:
        calc_mode = False
        if calc:
            calc.hide()
    # 新增：按 c 显示/隐藏计算器
    if key == ord('c'):
        if calc is None:
            calc = GestureCalculator(master=None, topmost=True)
        if calc_mode:
            calc.hide()
            calc_mode = False
        else:
            calc.show()
            calc_mode = True
    # 显示/隐藏快速指南
    if key == ord('h'):
        show_quick_guide = not show_quick_guide
    if key == ord('q'):
        break
################################## ↑ 主循环 ↑ ##################################

cap.release()
cv2.destroyAllWindows()