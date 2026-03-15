#写生命控制逻辑
import asyncio
import json
import re
import socket
import threading
import time
from queue import Queue

import pymem
import pymem.process
import websockets

class Message:
    target_ID = None
    client_ID = None

qr_event = threading.Event()
qr_client_id = None

PROCESS_NAME = "Buckshot Roulette.exe"

BASE_OFFSET = 0x035AD2C0
OFFSETS = [0x318, 0x0, 0x68, 0x28, 0x110]

WS_URI = "ws://127.0.0.1:9999"

event_queue = Queue()
stop_flag = False


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def resolve_pointer(pm, module_base):

    addr = module_base + BASE_OFFSET

    # 第一层：先 +318 再读
    addr = pm.read_longlong(addr)
    addr = pm.read_longlong(addr + OFFSETS[0])

    # 中间层
    for off in OFFSETS[1:-1]:
        addr = pm.read_longlong(addr + off)
        if addr == 0:
            raise Exception("指针断链")

    # 最后一层
    final_addr = addr + OFFSETS[-1]

    return final_addr


def memory_polling_loop():
    global stop_flag

    print("等待游戏进程启动...")

    pm = None
    while not pm:
        try:
            pm = pymem.Pymem(PROCESS_NAME)
        except:
            time.sleep(1)

    print("已连接游戏")

    module = pymem.process.module_from_name(
        pm.process_handle,
        PROCESS_NAME
    ).lpBaseOfDll

    final_addr = None
    last_value = 0

    while not stop_flag:
        try:

            if final_addr is None:
                print("重新解析指针链...")
                final_addr = resolve_pointer(pm, module)

                last_value = pm.read_int(final_addr)

                print("定位成功:", hex(final_addr))

                global qr_client_id
                qr_client_id = hex(final_addr)  # 或你想用的 client_id
                qr_event.set()

            value = pm.read_int(final_addr)

            if value != last_value:
                event_queue.put((last_value, value))
                print("生命变化:", last_value, "->", value)
                last_value = value

        except Exception as e:
            final_addr = None
            time.sleep(0.3)

        time.sleep(0.01)


async def websocket_loop():

    while True:
        try:
            async with websockets.connect(WS_URI) as ws:

                print("websocket 已连接")

                while True:

                    # # ⭐⭐⭐ 在这里检测二维码事件
                    # if qr_event.is_set():
                    #     qr_event.clear()
                    #     await generate_qr_code(qr_client_id)

                    message = await ws.recv()
                    print(f"收到消息: {message}")

                    # 检查消息是否为空
                    if not message:
                        print("收到空消息。")
                        continue

                    # 解析消息
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        print(f"JSONDecodeError: 无法解析消息: {message}")
                        continue  # 跳过对该消息的进一步处理

                    # 其他消息处理逻辑
                    if data.get("type") == "bind" and data.get("message") == "targetId":
                        client_id = data["clientId"]
                        print(f"客户端 ID: {client_id}")
                        Message.client_ID = client_id
                        if qr_event.is_set():
                            qr_event.clear()
                            await generate_qr_code(client_id)

                    if not event_queue.empty():

                        old, new = event_queue.get()
                        diff = new - old

                        print(f"内存值变化: {diff}")

                        # ⭐⭐⭐ 生命减少
                        if diff < 0:

                            strength = abs(diff) * 10

                            msg = {
                                "type": 2,
                                "strength": strength,
                                "channel": 1,
                                "clientId": Message.client_ID,
                                "targetId": Message.target_ID
                            }

                            await ws.send(json.dumps(msg))

                            # ⭐ 波形
                            pulse = {
                                "type": "clientMsg",
                                "time": 30,
                                "channel": "A",
                                "clientId": Message.client_ID,
                                "targetId": Message.target_ID,
                                "message": "A:[\"0A0A0A0A00000000\",\"0A0A0A0A0A0A0A0A\",\"0A0A0A0A14141414\",\"0A0A0A0A1E1E1E1E\",\"0A0A0A0A28282828\",\"0A0A0A0A32323232\",\"0A0A0A0A3C3C3C3C\",\"0A0A0A0A46464646\",\"0A0A0A0A50505050\",\"0A0A0A0A5A5A5A5A\",\"0A0A0A0A64646464\"]"
                            }

                            await ws.send(json.dumps(pulse))

                        # ⭐⭐⭐ 生命恢复
                        elif diff > 0:

                            msg = {
                                "type": 1,
                                "strength": diff * 10,
                                "channel": 1,
                                "clientId": Message.client_ID,
                                "targetId": Message.target_ID
                            }

                            await ws.send(json.dumps(msg))

                    await asyncio.sleep(0.001)

        except:
            print("ws断开，重连中...")
            await asyncio.sleep(1)


async def generate_qr_code(client_id):

    import qrcode
    import tkinter as tk
    from PIL import ImageTk

    header = f"https://www.dungeon-lab.com/app-download.php#DGLAB-SOCKET#ws://{get_host_ip()}:9999/"
    print(header)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(header + client_id)
    print(client_id)
    qr.make(fit=True)


    img = qr.make_image(fill_color="black", back_color="white")

    def show():
        root = tk.Tk()
        root.title("QR")

        img_tk = ImageTk.PhotoImage(img)
        label = tk.Label(root, image=img_tk)
        label.image = img_tk
        label.pack()

        root.mainloop()

    # ⭐ 放线程里避免卡 asyncio
    threading.Thread(target=show, daemon=True).start()

async def main():

    t = threading.Thread(
        target=memory_polling_loop,
        daemon=True
    )
    t.start()

    await websocket_loop()


if __name__ == "__main__":
    asyncio.run(main())