import tkinter as tk
from PIL import ImageTk
import queue

ui_queue = queue.Queue()

def ui_loop():

    root = tk.Tk()
    root.title("Control Panel")

    label = tk.Label(root)
    label.pack()

    def poll():

        try:
            img = ui_queue.get_nowait()

            img_tk = ImageTk.PhotoImage(img)
            label.config(image=img_tk)
            label.image = img_tk

        except queue.Empty:
            pass

        root.after(50, poll)

    poll()
    root.mainloop()