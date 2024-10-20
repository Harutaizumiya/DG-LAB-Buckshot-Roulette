import time
from idlelib.pyparse import trans

import pymem
import pymem.process

# 配置模块名称、基址偏移和多级偏移量
PROCESS_NAME = "Buckshot Roulette.exe"  # 目标进程名
BASE_OFFSET = 0x03593E40  # 模块内的偏移量
OFFSETS = [0x68, 0x368, 0x18, 0x3B0, 0x10, 0x30, 0x68, 0x28, 0x110]  # 多级指针偏移量

last_value = None  # 保存上次读取的值

def get_pointer_address(pm, base_address, offsets):
    """解析多级指针路径，检查每一级是否为有效地址"""
    try:
        address = pm.read_longlong(base_address)  # 读取基址指针
        print(f"初始地址: {hex(address)}")

        for i, offset in enumerate(offsets):
            if address is None:
                raise ValueError(f"无法读取偏移 {i}: {hex(offset)}")
            address = pm.read_longlong(address + offset)  # 逐级解析
            print(f"偏移 {i}: 地址 = {hex(address)}")

        return address
    except pymem.exception.MemoryReadError as e:
        print(f"内存读取失败: {e}")
        return None


def main():
    global last_value

    # 打开目标进程
    while True:
        try:
            pm = pymem.Pymem(PROCESS_NAME)
            print(f"成功连接到 {PROCESS_NAME}")
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

    print(f"开始监控地址: {hex(base_address)}")

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
                print(f"读取到的当前值: {current_value}")
            except pymem.exception.MemoryReadError as e:
                print(f"读取内存失败: {e}")
                continue

            # 检查值是否发生变化
            if current_value != last_value:
                print(f"值发生变化！新值: {current_value}")
                last_value = current_value

            time.sleep(0.5)  # 每 500 毫秒检查一次
    except KeyboardInterrupt:
        print("监控已停止")
    finally:
        pm.close_process()


if __name__ == "__main__":
    main()
