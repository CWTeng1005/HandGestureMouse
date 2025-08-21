import cv2
from collections import deque
import mediapipe as mp

def fingers_up(lm, handedness: str):
    """
    仅用坐标判断手指是否伸直：
    - 拇指：Right => tip(4).x < mcp(2).x ；Left => tip(4).x > mcp(2).x
    - 其余四指：tip(i).y < pip(i-2).y
    返回 [T, I, M, R, P] （1=伸直，0=弯曲）
    """
    I = int(lm[8].y  < lm[6].y)
    M = int(lm[12].y < lm[10].y)
    R = int(lm[16].y < lm[14].y)
    P = int(lm[20].y < lm[18].y)
    if handedness == "Right":
        T = int(lm[4].x < lm[2].x)
    else:
        T = int(lm[4].x > lm[2].x)
    return [T, I, M, R, P]

# 左手数字规则
# T, I, M, R, P --> 拇指，食指，中指，无名指，小指
DIGIT_RULES = {
    1: dict(up=set("I"),     down=set("TMRP")),
    2: dict(up=set("IM"),    down=set("TRP")),
    3: dict(up=set("IMR"),   down=set("TP")),
    4: dict(up=set("IMRP"),  down=set("T")),
    5: dict(up=set("TIMRP"), down=set()),
    6: dict(up=set("TP"),    down=set("IMR")),
    7: dict(up=set("TI"),    down=set("MRP")),
    8: dict(up=set("TIM"),   down=set("RP")),
    9: dict(up=set("TIMR"),  down=set("P")),
    0: dict(up=set("TMRP"),  down=set("I")),
}

class LeftDigitRecognizer:
    """
    左手专用数字识别（右手继续当鼠标）。
    流程极简：
      - 必须先“左手全收拳”连续 rearm_frames 帧 上膛
      - 上膛后做一个数字手势；稳定 stable_frames 帧后仅输出一位
      - 输出后立刻关闸；必须再次全收拳才能继续下一位
    """
    def __init__(self,
                 stable_frames=6,
                 rearm_frames=3,
                 invert_handedness=False,
                 debug=False):
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=2, model_complexity=1,
            min_detection_confidence=0.7, min_tracking_confidence=0.6
        )
        self.stable_hist = deque(maxlen=stable_frames)
        self.rearm_hist  = deque(maxlen=rearm_frames)
        self._armed      = False
        self.invert_handedness = bool(invert_handedness)
        self.debug = bool(debug)

    @staticmethod
    def _match(bits, need_up:set, need_down:set):
        for k in need_up:
            if not bits[k]: return False
        for k in need_down:
            if bits[k]: return False
        return True

    def _digit_from_left(self, lm):
        T, I, M, R, P = fingers_up(lm, "Left")
        bits = {"T":bool(T), "I":bool(I), "M":bool(M), "R":bool(R), "P":bool(P)}
        for d, rule in DIGIT_RULES.items():
            if self._match(bits, rule["up"], rule.get("down", set())):
                return d, bits
        return None, bits

    def update(self, bgr_image):
        """
        输入：BGR 帧
        输出：digit（int 或 None）
        """
        h, w = bgr_image.shape[:2]
        res = self.hands.process(cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB))

        left_lm = None
        if res.multi_hand_landmarks and res.multi_handedness:
            for lm, hd in zip(res.multi_hand_landmarks, res.multi_handedness):
                label = hd.classification[0].label  # 'Left'/'Right'
                if self.invert_handedness:
                    label = "Left" if label == "Right" else "Right"
                if label == "Left":
                    left_lm = lm.landmark
                    break

        # 没抓到左手：清空状态
        if left_lm is None:
            self.stable_hist.clear()
            self.rearm_hist.clear()
            return None

        # 上膛：全收拳 连续 N 帧
        cnt = sum(fingers_up(left_lm, "Left"))
        self.rearm_hist.append(cnt == 0)
        if len(self.rearm_hist) == self.rearm_hist.maxlen and all(self.rearm_hist):
            self._armed = True

        # 识别并稳定
        d, bits = self._digit_from_left(left_lm)
        self.stable_hist.append(d)

        out_digit = None
        if self._armed and cnt > 0:
            if len(self.stable_hist) == self.stable_hist.maxlen and len(set(self.stable_hist)) == 1:
                stable_d = self.stable_hist[0]
                if stable_d is not None:
                    out_digit = stable_d
                    self._armed = False
                    self.rearm_hist.clear()   # 输出后必须再回拳

        if self.debug:
            txt = f"L fist_cnt0:{int(cnt==0)} armed:{int(self._armed)} d:{d}"
            cv2.putText(bgr_image, txt, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)

        return out_digit