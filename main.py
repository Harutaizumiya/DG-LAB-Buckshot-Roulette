import queue
import time
import threading
from ui_manager import ui_loop
from ui_manager import ui_queue
import json
from qrcode.main import QRCode
from qr_server import QRCodeServer
from ws_client import ReconnectingWSClient
from memory_listener import MemoryListener
from state import RuntimeState

threading.Thread(target=ui_loop, daemon=True).start()

PROCESS_NAME = "Buckshot Roulette.exe"
BASE_OFFSET = 0x035AD2C0
OFFSETS = [0x318, 0x0, 0x68, 0x28, 0x110]


# ========= 全局事件队列 =========
message_queue = queue.Queue()
event_queue = queue.Queue()


# ========= WS回调 =========
def on_msg_received(msg):
    message_queue.put(msg)


# ========= 内存回调 =========
def hp_changed(old, new):
    event_queue.put((old, new))


# ========= 启动 WS =========
client = ReconnectingWSClient(
    "ws://127.0.0.1:9999",
    on_message_callback=on_msg_received
)
client.start()


# ========= 启动内存监听 =========
listener = MemoryListener(
    PROCESS_NAME,
    BASE_OFFSET,
    OFFSETS,
    on_change=hp_changed
)
listener.start()


qr_server = QRCodeServer(port=9999)

print("系统已启动")


# ========= 主事件循环 =========
try:
    while True:

        # ===== 处理 WS 消息 =====
        try:
            msg = message_queue.get_nowait()
            print("收到WS:", msg)

            # 可以在这里：
            # → 控制外挂
            # → AI决策
            # → 修改内存
            if isinstance(msg, str):
                data = json.loads(msg)
            else:
                data = msg

                # ⭐ 判断 bind
            if data.get("type") == "bind":
                RuntimeState.client_id = data.get("clientId")
                RuntimeState.target_id = data.get("targetId")

                if RuntimeState.client_id:
                    print("✅ 收到 clientId:", RuntimeState.client_id)

                    img, url = qr_server.generate_img(RuntimeState.client_id)
                    ui_queue.put(img)

                    print("📱 已生成二维码:", url)

        except queue.Empty:
            pass

        # ===== 处理生命变化 =====
        try:
            old, new = event_queue.get_nowait()
            print("HP变化:", old, new)

            # 示例：自动发送给服务器

            diff = new - old
            if diff <0 :
                strength = abs(diff) * 10

                msg = {
                    "type": 2,
                    "strength": strength,
                    "message": "set channel",
                    "channel": 1,
                    "clientId": RuntimeState.client_id,
                    "targetId": RuntimeState.target_id
                }

                client.send(json.dumps(msg))

                # ⭐ 波形
                pulse = {
                    "type": "clientMsg",
                    "time": 30,
                    "channel": "A",
                    "clientId": RuntimeState.client_id,
                    "targetId": RuntimeState.target_id,
                    "message": "A:[\"0A0A0A0A00000000\",\"0A0A0A0A0A0A0A0A\",\"0A0A0A0A14141414\",\"0A0A0A0A1E1E1E1E\",\"0A0A0A0A28282828\",\"0A0A0A0A32323232\",\"0A0A0A0A3C3C3C3C\",\"0A0A0A0A46464646\",\"0A0A0A0A50505050\",\"0A0A0A0A5A5A5A5A\",\"0A0A0A0A64646464\"]"
                }

                client.send(json.dumps(pulse))

        except queue.Empty:
            pass

        # ===== 主程序其他逻辑 =====
        time.sleep(0.01)

except KeyboardInterrupt:
    print("退出中")