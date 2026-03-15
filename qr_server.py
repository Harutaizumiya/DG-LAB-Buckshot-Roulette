import socket
import qrcode

class QRCodeServer:

    def __init__(self, port=9999):
        self.port = port

    def get_host_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    def generate_img(self, client_id):

        header = (
            "https://www.dungeon-lab.com/app-download.php"
            "#DGLAB-SOCKET#"
            f"ws://{self.get_host_ip()}:{self.port}/"
        )

        data = header + client_id

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        return img, data