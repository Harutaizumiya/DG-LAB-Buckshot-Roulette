import asyncio
import json
import re
import time
from socket import socket
from time import sleep

import pymem
import websockets
import qrcode
import tkinter as tk

from PIL import ImageTk

#根据需要改变socket服务器端口
uri = "ws://localhost:9999"

PROCESS_NAME = "Buckshot Roulette.exe"  # 目标进程名

##########请注意！，修改以下两个变量！###########
BASE_OFFSET = 123  # 模块内的偏移量
OFFSETS = []  # 多级指针偏移量

last_value = None  # 保存上次读取的值
websocket = None
class Message:
    target_ID = None
    client_ID = None


def get_pointer_address(pm, base_address, offsets):
    """解析多级指针路径，检查每一级是否为有效地址"""
    try:
        address = pm.read_longlong(base_address)  # 读取基址指针
        #print(f"初始地址: {hex(address)}")

        for i, offset in enumerate(offsets):
            if address is None:
                raise ValueError(f"无法读取偏移 {i}: {hex(offset)}")
            address = pm.read_longlong(address + offset)  # 逐级解析
            #print(f"偏移 {i}: 地址 = {hex(address)}")

        return address
    except pymem.exception.MemoryReadError as e:
        print(f"内存读取失败: {e}")
        return None

async def health():
    global last_value

    # 打开目标进程
    while True:
        try:
            pm = pymem.Pymem(PROCESS_NAME)
            # print(f"成功连接到 {PROCESS_NAME}")
            break  # 成功连接，退出循环
        except pymem.exception.ProcessNotFound:
            print("目标程序似乎不在运行中。")
        except Exception as e:
            print(f"发生错误: {e}")

        # 提示用户选择是否重试或退出
        keyboard_input = input("请打开目标程序，输入 'r' 来重试，输入 'q' 退出程序: ").strip().lower()
        if keyboard_input == "q":
            print("程序已退出。")
            exit()  # 用户选择退出
        elif keyboard_input != "r":
            print("无效输入，请重试。")

        time.sleep(1)  # 避免循环过快，稍作延迟

    module = pymem.process.module_from_name(pm.process_handle, PROCESS_NAME)
    base_address = module.lpBaseOfDll + BASE_OFFSET  # 计算目标基址

    # print(f"开始监控地址: {hex(base_address)}")

    try:
        while True:
            # 解析多级指针路径的最终地址
            target_address = get_pointer_address(pm, base_address, OFFSETS)
            if target_address is None:
                print("无法解析指针地址，跳过本次循环")
                time.sleep(0.5)
                continue

            # 读取最终地址的值，确保读取整型
            try:
                current_value = target_address
                # print(f"读取到的当前值: {current_value}")
            except pymem.exception.MemoryReadError as e:
                print(f"读取内存失败: {e}")
                continue

            # 检查值是否发生变化
            if current_value != last_value:
                # print(f"值发生变化！新值: {current_value}")
                last_value = current_value

            time.sleep(0.5)  # 每 500 毫秒检查一次
            return current_value
    except KeyboardInterrupt:
        print("监控已停止")
    finally:
        pm.close_process()



async def generate_qr_code(client_id):
    # 创建二维码对象
    header = "https://www.dungeon-lab.com/app-download.php#DGLAB-SOCKET#ws://192.168.5.7:9999/"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(header+client_id)
    print(header+client_id)
    qr.make(fit=True)

    # 生成二维码图像 (PIL 格式)
    img = qr.make_image(fill_color="black", back_color="white")

    # 初始化 Tkinter 窗口
    root = tk.Tk()
    root.title("二维码生成")

    # 将 PIL 图像转换为 Tkinter 可显示的格式
    img_tk = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=img_tk)
    label.image = img_tk  # 避免图像被垃圾回收
    label.pack()

    # 运行主循环
    root.mainloop()


async def change_strength():
    last_health = await health()
    while True:
        await asyncio.sleep(1)  # 每秒检查一次
        global websocket

        current_health = await health()
        if current_health != last_health:
            health_difference = current_health-last_health
            print(f"内存值已变化: {health_difference}")
            # 如果值发生变化，发送消息
            if health_difference == -1:
                print("强度+10")
                strength_message = {"type":2,"strength":10,"message":"set channel","channel": 1,"clientId":Message.client_ID,"targetId":Message.target_ID}
                json_strength_message = json.dumps(strength_message)
                await websocket.send(json_strength_message)
                #如何发送波形信息？
                pulse_message = {"type":"clientMsg","time":30,"channel":"A","clientId":Message.client_ID,"targetId":Message.target_ID,"message":"A:[\"0A0A0A0A00000000\",\"0A0A0A0A0A0A0A0A\",\"0A0A0A0A14141414\",\"0A0A0A0A1E1E1E1E\",\"0A0A0A0A28282828\",\"0A0A0A0A32323232\",\"0A0A0A0A3C3C3C3C\",\"0A0A0A0A46464646\",\"0A0A0A0A50505050\",\"0A0A0A0A5A5A5A5A\",\"0A0A0A0A64646464\"]"}
                json_pulse_message = json.dumps(pulse_message)
                await websocket.send(json_pulse_message)
            elif health_difference == -2:
                print("强度+20")
                strength_message = {"type": 2, "strength": 20, "message": "set channel", "channel": 1,
                                    "clientId": Message.client_ID, "targetId": Message.target_ID}
                json_strength_message = json.dumps(strength_message)
                await websocket.send(json_strength_message)
                # 如何发送波形信息？
                pulse_message = {"type": "clientMsg", "time": 30, "channel": "A", "clientId": Message.client_ID,
                                 "targetId": Message.target_ID,
                                 "message": "A:[\"0A0A0A0A00000000\",\"0A0A0A0A0A0A0A0A\",\"0A0A0A0A14141414\",\"0A0A0A0A1E1E1E1E\",\"0A0A0A0A28282828\",\"0A0A0A0A32323232\",\"0A0A0A0A3C3C3C3C\",\"0A0A0A0A46464646\",\"0A0A0A0A50505050\",\"0A0A0A0A5A5A5A5A\",\"0A0A0A0A64646464\"]"}
                json_pulse_message = json.dumps(pulse_message)
                await websocket.send(json_pulse_message)
                #生命值回复时降低10强度
            elif health_difference == 1:
                print("强度-10")
                strength_message = {"type": 1, "strength": 10, "message": "set channel", "channel": 1,
                                    "clientId": Message.client_ID, "targetId": Message.target_ID}
                json_strength_message = json.dumps(strength_message)
                await websocket.send(json_strength_message)
                # 如何发送波形信息？



            last_health = current_health  # 更新最后值




# 输入要生成的二维码内容
#text = input("请输入要生成的二维码内容：")
#generate_qr_code(text)
# 心跳包的间隔时间（秒）
HEARTBEAT_INTERVAL = 1
# 检测心跳包的超时时间（秒）
HEARTBEAT_TIMEOUT = 10

async def client():
    uri = "ws://192.168.5.7:9999"  # SOCKET 服务器地址
    global websocket
    async with websockets.connect(uri) as websocket:
        # 记录上次收到心跳包的时间
        last_heartbeat = time.time()

        async def heartbeat_checker():
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                current_time = time.time()
                # 检查是否超时
                if current_time - last_heartbeat > HEARTBEAT_TIMEOUT:
                    print("心跳超时！连接可能已丢失。")
                    # 在这里可以选择关闭连接或尝试重新连接
                    break

        # 启动心跳检查器
        await asyncio.create_task(heartbeat_checker())

        while True:
            try:
                # 接收来自服务器的消息
                message = await websocket.recv()
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

                # 检查消息类型，更新心跳状态
                if data.get("type") == "heartbeat":
                    last_heartbeat = time.time()  # 更新最后收到心跳包的时间
                    print("收到心跳包。")

                # 其他消息处理逻辑
                elif data.get("type") == "bind" and data.get("message") == "targetId":
                    client_id = data["clientId"]
                    print(f"客户端 ID: {client_id}")
                    Message.client_ID = client_id
                    await generate_qr_code(client_id)

                elif data.get("type") == "bind" and data.get("message") == "200":
                    target_id = data["targetId"]
                    print(f"目标 ID: {target_id}")
                    Message.target_ID = target_id

                elif data.get("type") == "msg":
                    # 使用正则表达式提取 message 中的数字
                    numbers = re.findall(r'\d+', data.get("message"))
                    print(numbers)

            except websockets.exceptions.ConnectionClosed:
                print("连接已关闭。")
                break
            except Exception as e:
                print(f"发生意外错误: {e}")

            except KeyboardInterrupt:
                print("用户退出")
async def main():
    # 使用 asyncio.gather 来并发运行 client 和 change_strength
    await asyncio.gather(
        client(),           # WebSocket 连接任务
        change_strength()   # 健康值监控任务
    )

# 运行主程序
if __name__ == '__main__':
    asyncio.run(main())
