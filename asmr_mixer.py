
import pygame
import threading
import os
import random
import sys  # <-- added

# -------- helper for PyInstaller bundled data (UI-PRESERVING) --------
def resource_path(rel_path):
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    return os.path.join(base, rel_path)

# 初始化 pygame
pygame.init()
pygame.mixer.init()

# 设置窗口大小为全屏
screen_width, screen_height = 1920, 1080
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
pygame.display.set_caption("Pluck String")

# 设置透明窗口（Windows 特定，需要 pywin32）
import win32gui, win32con
hwnd = pygame.display.get_wm_info()['window']
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                        win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST)
win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 255, win32con.LWA_COLORKEY)

# 加载音效（仅改动路径解析，UI 逻辑完全不变）
SOUND_FOLDER = 'SE'
SOUND_FILES = [
    'books.mp3', 'bubbles.mp3', 'fire.mp3', 'ocean.mp3', 'rain.mp3', 'river.mp3', 'windbell.mp3'
]
# 原来: SOUND_PATHS = [os.path.join(SOUND_FOLDER, f) for f in SOUND_FILES]
SOUND_PATHS = [resource_path(os.path.join(SOUND_FOLDER, f)) for f in SOUND_FILES]
SOUND_EMOJIS = ['📚', '🫧', '🔥', '🌊', '🌧️', '🏞️', '🎐']

# 播放器和状态
effect_players = [None] * 7
active_sounds = []

# 字体
font = pygame.font.SysFont("Arial", 36)
emoji_font = pygame.font.SysFont("Segoe UI Emoji", 48)

# 初始化线条
lines = []
for i in range(7):
    x = 250 + i * 200
    lines.append({
        'x': x,
        'y1': 0,
        'y2': 600,
        'active': False,
        'offset': 0,
        'shake_dir': 1,
        'sparkles': []
    })

def play_sound(index):
    if effect_players[index] is None:
        effect_players[index] = pygame.mixer.Sound(SOUND_PATHS[index])  # 仅路径变化
        effect_players[index].set_volume(0.8)
    if SOUND_FILES[index] not in active_sounds:
        if len(active_sounds) >= 3:
            oldest = active_sounds.pop(0)
            stop_sound(SOUND_FILES.index(oldest))
        active_sounds.append(SOUND_FILES[index])
        effect_players[index].play(-1)

def stop_sound(index):
    if effect_players[index]:
        effect_players[index].stop()
    if SOUND_FILES[index] in active_sounds:
        active_sounds.remove(SOUND_FILES[index])

def stop_all():
    for i in range(7):
        stop_sound(i)

def run_game():
    running = True
    clock = pygame.time.Clock()

    while running:
        screen.fill((0, 0, 0))

        # 画线条和emoji（完全保留原有 UI 和逻辑）
        for i, line in enumerate(lines):
            sound_name = SOUND_FILES[i]
            persistent = sound_name in active_sounds

            if persistent:
                line['active'] = True
            elif not persistent:
                line['active'] = False

            color = (219, 202, 196) if line['active'] else (166, 175, 166)
            x = line['x']

            if line['active']:
                line['offset'] += line['shake_dir'] * 2
                if abs(line['offset']) > 10:
                    line['shake_dir'] *= -1
            else:
                line['offset'] = 0

            pygame.draw.line(screen, color, (x + line['offset'], line['y1']), (x + line['offset'], line['y2']), 5)

            # emoji 贴图
            try:
                emoji_surf = emoji_font.render(SOUND_EMOJIS[i], True, (255, 255, 255))
                screen.blit(emoji_surf, (x - 20, line['y2'] + 10))
            except:
                pygame.draw.rect(screen, (255, 255, 255), (x - 10, line['y2'] + 10, 20, 20))

            # sparkle
            if line['active'] and random.random() < 0.2:
                line['sparkles'].append([x + line['offset'], random.randint(line['y1'], line['y2']), random.randint(2, 4)])
            new_sparkles = []
            for s in line['sparkles']:
                pygame.draw.circle(screen, (255, 255, 255), (s[0], s[1]), s[2])
                s[1] -= 2
                if s[1] > line['y1']:
                    new_sparkles.append(s)
            line['sparkles'] = new_sparkles

        # 合成器按钮
        synth_buttons = []
        for i in range(3):
            if i < len(active_sounds):
                name = active_sounds[i].replace('.mp3', '')
                btn = pygame.Rect(700 + i * 150, 880, 120, 40)
                pygame.draw.rect(screen, (74, 112, 139), btn)
                text = font.render(name, True, (250, 255, 240))
                text_rect = text.get_rect(center=btn.center)
                screen.blit(text, text_rect)
                synth_buttons.append((btn, i))
            else:
                btn = pygame.Rect(700 + i * 150, 880, 120, 40)
                pygame.draw.rect(screen, (74, 112, 139), btn)
                empty = font.render("Empty", True, (250, 255, 240))
                empty_rect = empty.get_rect(center=btn.center)
                screen.blit(empty, empty_rect)

        # 清空/退出按钮
        clear_btn = pygame.Rect(1550, 880, 100, 50)
        exit_btn = pygame.Rect(1670, 880, 100, 50)
        pygame.draw.rect(screen, (112, 128, 105), clear_btn)
        pygame.draw.rect(screen, (112, 128, 105), exit_btn)
        clear = font.render("Clear", True, (250, 255, 240))
        exit = font.render("Exit", True, (250, 255, 240))
        clear_rect = clear.get_rect(center=clear_btn.center)
        exit_rect = exit.get_rect(center=exit_btn.center)
        screen.blit(clear, clear_rect)
        screen.blit(exit, exit_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if clear_btn.collidepoint(event.pos):
                    stop_all()
                elif exit_btn.collidepoint(event.pos):
                    stop_all()
                    running = False
                for btn, idx in synth_buttons:
                    if btn.collidepoint(event.pos):
                        stop_sound(SOUND_FILES.index(active_sounds[idx]))

        # 碰撞检测
        mx, my = pygame.mouse.get_pos()
        for i, line in enumerate(lines):
            x = line['x']
            if abs(mx - x) < 15 and line['y1'] <= my <= line['y2']:
                if SOUND_FILES[i] not in active_sounds:
                    play_sound(i)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    threading.Thread(target=run_game, daemon=False).start()
