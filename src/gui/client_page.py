import tkinter as tk

class ClientFrame(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master

        # 这里添加客户端的组件
        tk.Label(self, text="客户端页面").pack(pady=20)
        tk.Button(self, text="返回", command=self.goto_main).pack(pady=10)

    def goto_main(self):
        from main_page import MainFrame
        self.master.show_frame(MainFrame)
