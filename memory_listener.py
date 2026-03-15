import time
import threading
import pymem
import pymem.process


class MemoryListener:

    def __init__(
            self,
            process_name,
            base_offset,
            offsets,
            on_change=None,     # 回调函数
            poll_interval=0.01
    ):
        self.process_name = process_name
        self.base_offset = base_offset
        self.offsets = offsets
        self.on_change = on_change
        self.poll_interval = poll_interval

        self._thread = None
        self._running = False

        self.pm = None
        self.module = None
        self.final_addr = None
        self.last_value = None

    # ========= 指针链解析 =========
    def _resolve_pointer(self):
        addr = self.module + self.base_offset

        addr = self.pm.read_longlong(addr)
        addr = self.pm.read_longlong(addr + self.offsets[0])

        for off in self.offsets[1:-1]:
            addr = self.pm.read_longlong(addr + off)
            if addr == 0:
                raise Exception("指针断链")

        return addr + self.offsets[-1]

    # ========= 连接进程 =========
    def _connect(self):
        while self._running and not self.pm:
            try:
                self.pm = pymem.Pymem(self.process_name)

                self.module = pymem.process.module_from_name(
                    self.pm.process_handle,
                    self.process_name
                ).lpBaseOfDll

                print("✅ 已连接游戏")

            except:
                time.sleep(1)

    # ========= 主循环 =========
    def _loop(self):

        print("⌛ 等待游戏启动...")
        self._connect()

        while self._running:

            try:

                if self.final_addr is None:
                    print("🔎 重新解析指针链")
                    self.final_addr = self._resolve_pointer()
                    self.last_value = self.pm.read_int(self.final_addr)

                    print("🎯 定位成功:", hex(self.final_addr))

                value = self.pm.read_int(self.final_addr)

                if value != self.last_value:

                    old = self.last_value
                    self.last_value = value

                    print("❤️ 生命变化:", old, "->", value)

                    if self.on_change:
                        self.on_change(old, value)

            except:
                self.final_addr = None
                time.sleep(0.3)

            time.sleep(self.poll_interval)

    # ========= 对外接口 =========
    def start(self):

        if self._thread:
            return

        self._running = True

        self._thread = threading.Thread(
            target=self._loop,
            daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False