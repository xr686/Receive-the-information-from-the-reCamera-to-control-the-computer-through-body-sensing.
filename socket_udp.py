import socket
import json
import time
from pynput.keyboard import Key, Controller
import threading
from collections import deque

# 键盘控制器
keyboard = Controller()

# 动作映射
key_map = {
    "left": Key.left,
    "right": Key.right,
    "jump": Key.up,
    "slide": Key.down
}

# 防抖和噪声滤除设置
ACTION_COOLDOWN = 0.3  # 动作冷却时间
NOISE_THRESHOLD = 5  # 噪声阈值，用于过滤小幅晃动
MIN_ACTION_DURATION = 0.1  # 最小动作持续时间

# 动作状态跟踪
last_action_time = 0
last_action = None
action_queue = deque(maxlen=10)  # 用于统计最近动作

# 滑动动作状态（防止连续触发）
slide_active = False
slide_timer = 0

# UDP 设置
UDP_IP = "0.0.0.0"
UDP_PORT = 5005

print(f"📡 正在监听 UDP 端口 {UDP_PORT}...")
print(f"⚙️  防抖间隔: {ACTION_COOLDOWN}秒")
print(f"⚙️  噪声阈值: {NOISE_THRESHOLD}")

# 创建 UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))


def filter_noise(current_action, current_time):
    """噪声滤除逻辑"""
    global last_action, last_action_time, action_queue

    # 如果没有动作，直接返回False
    if not current_action:
        return False

    # 检查时间间隔
    time_diff = current_time - last_action_time
    if time_diff < ACTION_COOLDOWN:
        # 检查是否为相同动作的连续触发
        if current_action == last_action:
            # 统计最近相同动作的频率
            recent_same_actions = sum(1 for act in list(action_queue)[-5:] if act == current_action)
            if recent_same_actions > 3:  # 如果最近5次中有4次是相同动作，可能是真实动作
                return True
            else:
                return False  # 过滤噪声
        else:
            return False  # 时间间隔不够，但动作不同，需要进一步判断

    # 添加动作到队列
    action_queue.append(current_action)

    # 检查是否为噪声（短时间内频繁变化的动作）
    if last_action and current_action != last_action:
        recent_actions = list(action_queue)[-5:]
        unique_actions = len(set(recent_actions))
        # 如果最近5次动作中有超过3种不同动作，可能是噪声
        if unique_actions > 2 and len(recent_actions) >= 5:
            action_changes = 0
            for i in range(1, len(recent_actions)):
                if recent_actions[i] != recent_actions[i - 1]:
                    action_changes += 1
            if action_changes > 3:  # 频繁变化，认为是噪声
                return False

    return True


def handle_slide_action():
    """处理滑动动作，防止连续触发"""
    global slide_active, slide_timer
    current_time = time.time()

    if not slide_active:
        slide_active = True
        slide_timer = current_time
        keyboard.press(key_map["slide"])
        print(f"✅ 执行动作: SLIDE    | 时间: {current_time:.2f}")
        return True
    else:
        # 滑动动作已激活，检查是否需要释放
        if current_time - slide_timer > 0.5:  # 滑动持续0.5秒后自动释放
            keyboard.release(key_map["slide"])
            slide_active = False
        return False  # 不需要再次触发


try:
    print("🎮 开始监听动作...")
    while True:
        data, addr = sock.recvfrom(1024)
        try:
            msg = json.loads(data.decode('utf-8'))
            action = msg.get("action")

            if not action or action not in key_map:
                continue

            current_time = time.time()

            # 应用噪声滤除逻辑
            if filter_noise(action, current_time):
                # 特殊处理滑动动作
                if action == "slide":
                    if handle_slide_action():
                        last_action_time = current_time
                        last_action = action
                else:
                    # 处理其他动作
                    if action != last_action or (current_time - last_action_time >= ACTION_COOLDOWN):
                        # 如果之前是滑动状态，先释放
                        if slide_active and last_action == "slide":
                            keyboard.release(key_map["slide"])
                            slide_active = False

                        # 执行键盘操作
                        key = key_map[action]
                        keyboard.press(key)
                        keyboard.release(key)

                        print(f"✅ 执行动作: {action.upper():8s} | 时间: {current_time:.2f}")

                        last_action_time = current_time
                        last_action = action
            else:
                # 噪声被滤除
                if action == "slide" and slide_active:
                    # 如果当前在滑动状态但收到噪声，检查是否需要结束滑动
                    if current_time - slide_timer > 1.0:  # 滑动太久自动结束
                        keyboard.release(key_map["slide"])
                        slide_active = False
                        print(f"⏹️  结束滑动   | 时间: {current_time:.2f}")

        except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
            print(f"⚠️ 无效数据包: {e}")

except KeyboardInterrupt:
    print("\n🛑 程序被用户终止")
finally:
    # 释放所有按键
    if slide_active:
        keyboard.release(key_map["slide"])
    sock.close()
    print("✅ UDP Socket 已关闭")