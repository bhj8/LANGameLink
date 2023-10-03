import asyncio
import ssl
import time
import websockets
import socket

class LANGameLink_426_client:

    def __init__(self, message_callback=None):
        self.message_callback = message_callback
        self.delay = 0.0  # in milliseconds
        self.SERVER_IPV6_ADDRESS = "::1"
        self.SERVER_PORT = 20000
        self.GAME_IPV4_ADDRESS = "127.0.0.1"
        self.GAME_TCP_PORTS = []
        self.GAME_UDP_PORTS = []
        

    def send_message(self, msg):
        if self.message_callback:
            self.message_callback(msg)


    def handle_websocket_errors(coro):
        async def wrapper(instance, *args, **kwargs):
            try:
                return await coro(instance, *args, **kwargs)
            except websockets.ConnectionClosedError:
                instance.send_message("WebSocket connection lost. Attempting to reconnect...")
        return wrapper

    @handle_websocket_errors
    async def central_websocket_receiver(self, websocket,udp_queue,tcp_queue,pong_queue):
        while True:
            message = await websocket.recv()
            prefix = message[:4]
            if prefix == b"UDP:":
                await udp_queue.put(message[4:])
            elif prefix == b"TCP:":
                await tcp_queue.put(message[4:])
            elif prefix == b"CNG:":
                await pong_queue.put(message[4:])
            elif prefix == b"SNG:":
                await websocket.send(message)

    @handle_websocket_errors
    async def send_ping(self, websocket):
        """不断发送PNG:消息给服务器"""
        while True:
            start_time = time.time()
            await websocket.send(b"CNG:"+str(start_time).encode())
            await asyncio.sleep(1)
    
    @handle_websocket_errors
    async def get_ping(self,pong_queue):
        """不断接收服务器发送的PNG:消息并计算延迟"""
        while True:
            pong = await pong_queue.get()
            remote_time = float(pong.decode())
            self.delay = time.time() - remote_time
            
    @handle_websocket_errors
    async def udp_receiver(self, websocket, udp_socket, udp_port,udp_queue):
        while True:
            data = await udp_queue.get()
            udp_socket.sendto(data, (self.GAME_IPV4_ADDRESS, udp_port))

    @handle_websocket_errors
    async def udp_sender(self, websocket, udp_socket):
        loop = asyncio.get_running_loop()
        while True:
            game_data, _ = await loop.sock_recv(udp_socket, 4096)
            await websocket.send(b"UDP:" + game_data)


    @handle_websocket_errors
    async def tcp_receiver(self, websocket, reader, tcp_port,tcp_queue):
        while True:
            data = await tcp_queue.get()
            reader.write(data)
            await reader.drain()

    @handle_websocket_errors
    async def tcp_sender(self, websocket, writer):
        while True:
            game_data = await writer.read(4096)
            await websocket.send(b"TCP:" + game_data)


    @handle_websocket_errors
    async def connect_to_websocket_server(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.load_verify_locations('certs/cert.pem')
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        while True:
            try:
                websocket = await websockets.connect(f"wss://[{self.SERVER_IPV6_ADDRESS}]:{self.SERVER_PORT}", ssl=ssl_context)
                self.send_message("Connected to WebSocket server successfully!")
                return websocket
            except Exception as e:
                self.send_message(f"Error connecting to WebSocket server: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(2)
    async def establish_tcp_connection(self, address, port):
        while True:
            try:
                reader, writer = await asyncio.open_connection(address, port)
                print(f"Connected to game client on port {port} successfully!")
                return reader, writer
            except ConnectionRefusedError:
                print(f"Failed to connect to game client on port {port}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def run(self):
        while True:
            websocket = await self.connect_to_websocket_server()
            
            udp_queue = asyncio.Queue()
            tcp_queue = asyncio.Queue()
            pong_queue = asyncio.Queue()
        
            task_list = []  # 用于存放任务
            udp_sockets = [] 

            task_list.append(asyncio.create_task(self.central_websocket_receiver(websocket,udp_queue,tcp_queue,pong_queue))) # 将中台添加到列表中
            
            task_list.append(asyncio.create_task(self.send_ping(websocket)))
            task_list.append(asyncio.create_task(self.get_ping(pong_queue)))
            
            for udp_port in self.GAME_UDP_PORTS:
                udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # udp_socket.setblocking(False)  # 设置为非阻塞
                udp_socket.bind((self.GAME_IPV4_ADDRESS, udp_port))  # 绑定到具体的端口上
                udp_sockets.append(udp_socket)
                
                task_list.append(asyncio.create_task(self.udp_receiver(websocket, udp_socket, udp_port,udp_queue)))
                task_list.append(asyncio.create_task(self.udp_sender(websocket, udp_socket)))

            for tcp_port in self.GAME_TCP_PORTS:
                reader, writer = await self.establish_tcp_connection(self.GAME_IPV4_ADDRESS, tcp_port)

                task_list.append(asyncio.create_task(self.tcp_receiver(websocket, reader, tcp_port,tcp_queue)))
                task_list.append(asyncio.create_task(self.tcp_sender(websocket, writer)))


                

            done, pending = await asyncio.wait(task_list, return_when=asyncio.FIRST_COMPLETED)

            for task in pending:
                task.cancel()

            self.send_message("Attempting to reconnect to the WebSocket server...")

if __name__ == "__main__":
    def gui_message_callback(msg):
        # 您可以在此函数中将消息传递给您的前端应用程序
        pass

    bridge = LANGameLink_426_client(message_callback=gui_message_callback)
    asyncio.run(bridge.run())
