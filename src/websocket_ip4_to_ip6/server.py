import asyncio
import time
import websockets
import socket
import ssl


class LANGameLink_426_server:

    def __init__(self, message_callback=None):
        self.IPV6_ADDRESS = "::"
        self.IPV6_PORT = 20000
        self.GAME_IPV4_ADDRESS = "127.0.0.1"
        self.GAME_TCP_PORTS = [123]
        self.GAME_UDP_PORTS = [123]   
        self.message_callback = message_callback 
        self.delays = {}
        
    def send_message(self, msg):
        if self.message_callback:
            self.message_callback(msg)

    async def measure_delay(self, websocket):
        """每秒测量与客户端的延迟"""
        while websocket.open:
            start_time = time.time()
            try:
                await websocket.ping()
                await asyncio.sleep(1)  # 等待1秒
                self.delays[websocket.remote_address] = time.time() - start_time
            except:
                break
    def handle_websocket_errors(coro):
        async def wrapper(*args, **kwargs):
            try:
                return await coro(*args, **kwargs)
            except websockets.ConnectionClosedError:
                print("WebSocket connection lost. Attempting to reconnect...")
        return wrapper


    @handle_websocket_errors
    async def udp_receiver(self, websocket, udp_socket):
        while True:
            game_data, _ = udp_socket.recvfrom(4096)
            await websocket.send(game_data)
            
    @handle_websocket_errors
    async def udp_sender(self, websocket, udp_socket, udp_port):  # 添加 udp_port 参数
        while True:
            data = await websocket.recv()
            udp_socket.sendto(data, (self.GAME_IPV4_ADDRESS, udp_port))  # 使用 udp_port

    @handle_websocket_errors
    async def tcp_receiver(self, websocket, reader):
        while True:
            game_data = await reader.read(4096)
            await websocket.send(game_data)

    @handle_websocket_errors
    async def tcp_sender(self, websocket, writer):
        while True:
            data = await websocket.recv()
            writer.write(data)
            await writer.drain()

    async def establish_tcp_connection(self, tcp_port):
        while True:
            try:
                reader, writer = await asyncio.open_connection(self.GAME_IPV4_ADDRESS, tcp_port)
                print("Connected to game client successfully!")
                return reader, writer
            except ConnectionRefusedError:
                print("Failed to connect to game client. Retrying in 5 seconds...")
                await asyncio.sleep(5)


async def handle_client(self, websocket, path):
    while True:
        try:
            print(f"Client {websocket.remote_address} connected!")

            task_list = []  # 此处我们创建一个新列表来存储任务
            udp_sockets = []  # 用于存储所有的UDP sockets

            # 处理UDP端口
            for udp_port in self.GAME_UDP_PORTS:
                udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                udp_socket.bind(('0.0.0.0', udp_port))  # 绑定到具体的端口上
                udp_sockets.append(udp_socket)
                task_list.append(asyncio.create_task(self.udp_receiver(websocket, udp_socket)))
                task_list.append(asyncio.create_task(self.udp_sender(websocket, udp_socket, udp_port)))

            # 处理TCP端口
            for tcp_port in self.GAME_TCP_PORTS:
                reader, writer = await self.establish_tcp_connection(tcp_port)
                task_list.append(asyncio.create_task(self.tcp_receiver(websocket, reader)))
                task_list.append(asyncio.create_task(self.tcp_sender(websocket, writer)))
                
                # 启动测量延迟的任务
                delay_task = asyncio.create_task(self.measure_delay(websocket))
                task_list.append(delay_task)

            done, pending = await asyncio.wait(task_list, return_when=asyncio.FIRST_COMPLETED)

            # 取消其它的任务
            for task in pending:
                task.cancel()

            # 关闭所有UDP sockets
            for udp_sock in udp_sockets:
                udp_sock.close()

            writer.close()
            await writer.wait_closed()

            # 从延迟字典中删除客户端的数据
            if websocket.remote_address in self.delays:
                del self.delays[websocket.remote_address]

            print(f"Client {websocket.remote_address} disconnected!")
            
        except websockets.ConnectionClosedError:
            print("WebSocket connection lost. Attempting to reconnect in 3 seconds...")
            await asyncio.sleep(3)


    async def run(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain('certs/cert.pem', 'certs/private_key.pem')
        server = await websockets.serve(self.handle_client, self.IPV6_ADDRESS, self.IPV6_PORT, ssl=ssl_context)
        print(f"WebSocket server started on ws://[{self.IPV6_ADDRESS}]:{self.IPV6_PORT}")
        await server.wait_closed()


if __name__ == "__main__":
    bridge = LANGameLink_426_server()
    asyncio.run(bridge.run())
