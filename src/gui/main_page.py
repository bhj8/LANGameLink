import tkinter as tk
from client_page import ClientFrame
from server_page import ServerFrame

class MainFrame(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.master.title("LANGameLink")

        tk.Button(self, text="我是客户端", command=self.goto_client).pack(pady=10)
        tk.Button(self, text="我是主机", command=self.goto_server).pack(pady=10)

    def goto_client(self):
        self.master.show_frame(ClientFrame)

    def goto_server(self):
        self.master.show_frame(ServerFrame)

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # 设置初始窗口大小为800x600并居中
        self.center_window(400, 300)

        self._frame = None
        self.show_frame(MainFrame)
        
    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.geometry(f'{width}x{height}+{x}+{y}')
        
    def show_frame(self, frame_class):
        if self._frame:
            self._frame.destroy()

        self._frame = frame_class(self)
        self._frame.pack(expand=True, fill="both")

if __name__ == "__main__":
    app = App()
    app.mainloop()
