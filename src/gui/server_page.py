import asyncio
import json
import threading
import tkinter as tk
from tkinter import ttk
from .input_validator import InputValidator
from .labeled_input import LabeledInput
from src.websocket_ip4_to_ip6.server import LANGameLink_426_server as Server
from .network_utils import network_utils_instance

class ServerFrame(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.server = Server(self.update_status)
        self.service_thread = None
        self.new_loop = None
        self.delay_update_id = None
        self.service_running = False
        
        self.server.IPV6_ADDRESS="自动获取中..."
        # 设置一个2秒后执行的延迟函数来更新IPV6_ADDRESS
        for _ in range(10):
            self.after(_ * 1000, self.update_ipv6_address)
        self.server.IPV6_PORT=network_utils_instance.available_port
        
        
        # 初始化动态端口字典
        self.dynamic_ports = {"TCP": self.server.GAME_TCP_PORTS, "UDP": self.server.GAME_UDP_PORTS} 
        
        # 初始化 IPv6 地址和端口
        self.inputs = [
            tk.Label(self, text="第一步：获取主机IP信息，并通过其它软件发送给客机")
        ]
        self.ipv6_address_input = LabeledInput(self, "主机IPv6地址", self.server.IPV6_ADDRESS, InputValidator.validate_ipv6)
        self.ipv6_port_input = LabeledInput(self, "主机IPv6端口", self.server.IPV6_PORT, InputValidator.validate_port)
        self.inputs.append(self.ipv6_address_input)
        self.inputs.append(self.ipv6_port_input)
        
       # 添加一个空行
        self.inputs.append(tk.Label(self, text=""))

        # 下拉菜单前的文本
        self.dropdown_label = tk.Label(self, text="第二步：选择需要联机的游戏")
        self.inputs.append(self.dropdown_label)

        # 加载游戏配置
        with open('games_config.json', 'r', encoding='utf-8') as file:
            self.games_config = json.load(file)

        # 创建下拉菜单
        self.game_var = tk.StringVar()
        self.dropdown = ttk.Combobox(self, textvariable=self.game_var, values=list(self.games_config.keys()))
        self.dropdown.bind("<<ComboboxSelected>>", self.load_game_config)
        self.inputs.append(self.dropdown)  # 将下拉菜单添加到self.inputs中

        # 下拉菜单下的警告文本
        self.warning_label = tk.Label(self, text="以下配置选择游戏后自动生成。没有要玩的游戏配置，请联系作者增加")
        self.inputs.append(self.warning_label)


        # 添加本地监听的 IP 地址
        self.ipv4_address_input = LabeledInput(self, "本地监听IP4", self.server.GAME_IPV4_ADDRESS, InputValidator.validate_ipv4,readonly=True)
        self.inputs.append(self.ipv4_address_input)

        # 初始化TCP端口
        for port in self.dynamic_ports["TCP"]:
            labeled_input = LabeledInput(self, f"本地游戏TCP端口", port, InputValidator.validate_port,readonly=True)
            self.inputs.append(labeled_input)

        # 初始化UDP端口
        for port in self.dynamic_ports["UDP"]:
            labeled_input = LabeledInput(self, f"本地游戏UDP端口", port, InputValidator.validate_port,readonly=True)
            self.inputs.append(labeled_input)

        # 为所有在 self.inputs 中的组件进行布局
        for index, inp in enumerate(self.inputs):
            inp.grid(row=index, column=0, sticky="w", padx=10, pady=5)
            
            
        # 创建并放置三个按钮
        btn_frame = tk.Frame(self)  # 按钮框架以确保按钮并排
        btn_frame.grid(row=len(self.inputs) + 1, column=0, pady=10)

        btn1 = tk.Button(btn_frame, text="开启服务", command=self.start_services, width=10)
        btn1.pack(side=tk.LEFT, padx=5)

        btn2 = tk.Button(btn_frame, text="强制中断", command=self.stop_services, width=10)
        btn2.pack(side=tk.LEFT, padx=5)

        btn3 = tk.Button(btn_frame, text=" 返回 ", command=self.goto_main, width=10)
        btn3.pack(side=tk.LEFT, padx=5)

        # 延迟显示栏
        self.delay_var = tk.StringVar(value="未连接")  # 初始显示未知延迟
        delay_label = tk.Label(self, textvariable=self.delay_var)
        delay_label.grid(row=len(self.inputs) + 2, column=0, pady=5)

        # 状态输入栏
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padx=10)  # relief和anchor使其看起来像状态栏
        self.status_label.grid(row=len(self.inputs) + 3, column=0, sticky=tk.EW, pady=5)

    def update_ipv6_address(self):
        self.server.IPV6_ADDRESS = network_utils_instance.ipv6_address
        self.ipv6_address_input.var.set(self.server.IPV6_ADDRESS)


    def load_game_config(self, event):
        game = self.game_var.get()
        config = self.games_config[game]

        # 清除旧的端口配置
        for inp in self.inputs[8:]:
            inp.grid_forget()
        self.inputs = self.inputs[:8]

        # 清除动态端口字典中的数据
        self.dynamic_ports = {"TCP": [], "UDP": []}

        # 加载新的端口配置
        for protocol, ports in config.items():
            for port in ports:
                inp = LabeledInput(self, f"本地游戏{protocol}端口", port, InputValidator.validate_port,readonly=True)
                self.dynamic_ports[protocol].append(inp)  # 存储到字典中
                self.inputs.append(inp)
        for index, inp in enumerate(self.inputs[5:], start=5):  # 重新布局，从下一个位置开始
            inp.grid(row=index, column=0, sticky="w", padx=10, pady=5)

    def update_status(self, message):
        self.status_var.set(message)
            
    def _update_Server_attr(self):
        self.server.GAME_IPV4_ADDRESS = self.ipv4_address_input.var.get()
        TCP_PORTS = []
        UDP_PORTS = []
        # 更新动态端口的值
        for protocol, inputs in self.dynamic_ports.items():
            for inp in inputs:
                if protocol == "TCP":
                    TCP_PORTS.append(int(inp.var.get()))
                else:
                    UDP_PORTS.append(int(inp.var.get()))
        self.server.GAME_TCP_PORTS = TCP_PORTS
        self.server.GAME_UDP_PORTS = UDP_PORTS
    def _start_delay_refresh_service(self):
        # 示例逻辑，实际实现可能会有所不同
        def update_delay():
            self.delay_var.set(f"延迟: {self.server.delays} ms")

            # 每秒更新一次延迟，并保持定时器的ID
            self.delay_update_id = self.after(1000, update_delay)

        update_delay()
    def _stop_delay_refresh_service(self):
        if self.delay_update_id:
            self.after_cancel(self.delay_update_id)
            self.delay_update_id = None
            
    def goto_main(self):
        self.stop_services()
        
        from .main_page import MainFrame
        self.master.show_frame(MainFrame)




    def start_asyncio_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def start_services(self):
        
        if self.service_running:
            print("Service is already running!")
            return

        self.service_running = True
        # 更新客户端属性
        self._update_Server_attr()

        # 启动延迟刷新服务（例如）
        self._start_delay_refresh_service()

        # 创建一个新的事件循环并在新的线程中运行它
        self.new_loop = asyncio.new_event_loop()
        self.service_thread = threading.Thread(target=self.start_asyncio_loop, args=(self.new_loop,), daemon=True)
        self.service_thread.start()

        # 将我们的协程安排到新的事件循环中
        asyncio.run_coroutine_threadsafe(self.server.run(), self.new_loop)

    def stop_services(self):
        self._stop_delay_refresh_service()
        try :
            # 取消所有的任务
            for task in asyncio.all_tasks(loop=self.new_loop):
                task.cancel()

            # 停止事件循环
            self.new_loop.call_soon_threadsafe(self.new_loop.stop)

            # 等待线程结束
            self.service_thread.join()
        except:
            pass
        
        
        self.status_var.set("已断开")
        self.delay_var.set("未连接")
        
        self.service_running = False