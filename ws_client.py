import websocket
import threading
import time


class ReconnectingWSClient:
    def __init__(self, url, on_message_callback=None):
        self.url = url
        self.on_message_callback = on_message_callback  # 用于把消息传回主程序
        self.ws = None
        self.retry_count = 0
        self.max_retries = 5
        self.running = True
        self.thread = threading.Thread(target=self._connection_manager)
        self.thread.daemon = True

    def _on_message(self, ws, message):
        # 如果主程序提供了处理函数，就调用它
        if self.on_message_callback:
            self.on_message_callback(message)

    def _on_error(self, ws, error):
        pass  # 可以在这里记录日志

    def _on_close(self, ws, close_status_code, close_msg):
        print("\n[WS] 连接已断开，准备重连...")

    def _on_open(self, ws):
        self.retry_count = 0
        print("\n[WS] 连接成功")

    def _connection_manager(self):
        while self.running:
            self.ws = websocket.WebSocketApp(
                self.url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            self.ws.run_forever(ping_interval=30)  # 增加心跳维持

            if self.running:
                self.retry_count += 1
                wait_time = 10 if self.retry_count > self.max_retries else 2
                time.sleep(wait_time)
                if self.retry_count > self.max_retries: self.retry_count = 0

    def start(self):
        self.thread.start()

    def send(self, data):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                self.ws.send(data)
                return True
            except:
                return False
        return False