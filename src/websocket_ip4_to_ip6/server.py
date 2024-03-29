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


    def handle_websocket_errors(coro):
        async def wrapper(*args, **kwargs):
            try:
                return await coro(*args, **kwargs)
            except websockets.ConnectionClosedError:
                print("WebSocket connection lost. Attempting to reconnect...")
        return wrapper
    
    @handle_websocket_errors
    async def central_websocket_receiver(self, websocket,udp_queue, tcp_queue,pong_queue):
        while True:
            message = await websocket.recv()
            prefix = message[:4]
            if prefix == b"UDP:":
                await udp_queue.put(message[4:])
            elif prefix == b"TCP:":
                await tcp_queue.put(message[4:])
            elif prefix == b"SNG:":
                await pong_queue.put(message[4:])
            elif prefix == b"CNG:":
                await websocket.send(message)

    @handle_websocket_errors
    async def send_ping(self, websocket):
        """不断发送SNG:消息给服务器"""
        while True:
            start_time = time.time()
            await websocket.send(b"SNG:"+str(start_time).encode())
            await asyncio.sleep(1)
    
    @handle_websocket_errors
    async def get_ping(self,websocket,pong_queue):
        """不断接收服务器发送的SNG:消息并计算延迟"""
        while True:
            pong = await pong_queue.get()
            old_time = float(pong.decode())
            self.delays[websocket.remote_address] = time.time() - old_time
    
    @handle_websocket_errors
    async def udp_receiver(self, websocket, udp_socket):
        loop = asyncio.get_running_loop()
        while True:
            game_data, _ = await loop.sock_recv(udp_socket, 4096)
            await websocket.send(b"UDP:" + game_data)

    @handle_websocket_errors
    async def udp_sender(self, udp_socket, udp_port,udp_queue):
        while True:
            data = await udp_queue.get()
            udp_socket.sendto(data, (self.GAME_IPV4_ADDRESS, udp_port))

    @handle_websocket_errors
    async def tcp_receiver(self, websocket, reader):
        while True:
            game_data = await reader.read(4096)
            await websocket.send(b"TCP:" + game_data)

    @handle_websocket_errors
    async def tcp_sender(self, writer,tcp_queue):
        while True:
            data = await tcp_queue.get()
            writer.write(data)
            await writer.drain()


    async def establish_tcp_connection(self, tcp_port):
        max_attempts = 5
        attempts = 0
        while True:
            try:
                reader, writer = await asyncio.open_connection(self.GAME_IPV4_ADDRESS, tcp_port)
                print("Connected to game client successfully!")
                return reader, writer
            except ConnectionRefusedError:
                attempts += 1
                if attempts > max_attempts:
                    print("Max attempts reached. Exiting establish_tcp_connection.")
                    return None, None
                print("Failed to connect to game client. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def handle_client(self, websocket, path):

        while True:
            try:
                print(f"Client {websocket.remote_address} connected!")
                
                udp_queue = asyncio.Queue()
                tcp_queue = asyncio.Queue()
                pong_queue = asyncio.Queue()                
                
                task_list = []  # 此处我们创建一个新列表来存储任务
                udp_sockets = []  # 用于存储所有的UDP sockets

                task_list.append(asyncio.create_task(self.central_websocket_receiver(websocket,udp_queue,tcp_queue,pong_queue))) # 将中台添加到列表中
                
                        # 启动测量延迟的任务
                task_list.append(asyncio.create_task(self.send_ping(websocket))  )
                task_list.append(asyncio.create_task(self.get_ping(websocket,pong_queue))  )
                
                # 处理UDP端口
                for udp_port in self.GAME_UDP_PORTS:
                    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    udp_socket.setblocking(False)  # 设置为非阻塞
                    udp_socket.bind((self.GAME_IPV4_ADDRESS, udp_port))  # 绑定到具体的端口上
                    udp_sockets.append(udp_socket)
                    
                    task_list.append(asyncio.create_task(self.udp_receiver(websocket, udp_socket)))
                    task_list.append(asyncio.create_task(self.udp_sender(udp_socket, udp_port,udp_queue)))

                # 处理TCP端口
                for tcp_port in self.GAME_TCP_PORTS:
                    reader, writer = await self.establish_tcp_connection(tcp_port)
                    task_list.append(asyncio.create_task(self.tcp_receiver(websocket, reader)))
                    task_list.append(asyncio.create_task(self.tcp_sender(writer,tcp_queue)))
                    


                done, pending = await asyncio.wait(task_list, return_when=asyncio.FIRST_COMPLETED)

                # 取消其它的任务
                for task in pending:
                    task.cancel()

                # 关闭所有UDP sockets
                for udp_sock in udp_sockets:
                    udp_sock.close()

                self.delays[websocket.remote_address]=None
                
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
        self.websocket_server = await websockets.serve(self.handle_client, self.IPV6_ADDRESS, self.IPV6_PORT, ssl=ssl_context)

        print(f"WebSocket server started on ws://[{self.IPV6_ADDRESS}]:{self.IPV6_PORT}")
        await self.websocket_server.wait_closed()


if __name__ == "__main__":
    bridge = LANGameLink_426_server()
    asyncio.run(bridge.run())
