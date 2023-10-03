import asyncio
import ssl
import websockets
import socket

class LANGameLink_426_client:

    def __init__(self, message_callback=None):
        self.message_callback = message_callback
        self.delay = 0.0  # in milliseconds
        self.SERVER_IPV6_ADDRESS = "::1"
        self.SERVER_PORT = 8765
        self.GAME_IPV4_ADDRESS = "127.0.0.1"
        self.GAME_TCP_PORTS = [123]
        self.GAME_UDP_PORTS = [123]

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
    async def udp_receiver(self, websocket, udp_socket, udp_port):
        while True:
            data = await websocket.recv()
            udp_socket.sendto(data, (self.GAME_IPV4_ADDRESS, udp_port))

    @handle_websocket_errors
    async def udp_sender(self, websocket, udp_socket):
        while True:
            game_data, _ = udp_socket.recvfrom(4096)
            await websocket.send(game_data)

    @handle_websocket_errors
    async def tcp_receiver(self, websocket, reader, tcp_port):
        while True:
            data = await websocket.recv()
            reader.write(data)
            await reader.drain()

    @handle_websocket_errors
    async def tcp_sender(self, websocket, writer):
        while True:
            game_data = await writer.read(4096)
            await websocket.send(game_data)

    async def measure_delay(self, websocket):
        while websocket.open:
            start_time = asyncio.get_event_loop().time()
            await websocket.ping()
            end_time = asyncio.get_event_loop().time()
            self.delay = (end_time - start_time) * 1000  # Convert to milliseconds
            await asyncio.sleep(1)  # measure delay every 10 seconds, adjust as needed

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
                asyncio.create_task(self.measure_delay(websocket))  # Start measuring delay
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
            tasks = []

            for udp_port in self.GAME_UDP_PORTS:
                udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                udp_socket.bind((self.GAME_IPV4_ADDRESS, udp_port))

                tasks.extend([
                    self.udp_receiver(websocket, udp_socket, udp_port),
                    self.udp_sender(websocket, udp_socket)
                ])

            for tcp_port in self.GAME_TCP_PORTS:
                reader, writer = await self.establish_tcp_connection(self.GAME_IPV4_ADDRESS, tcp_port)

                tasks.extend([
                    self.tcp_receiver(websocket, reader, tcp_port),
                    self.tcp_sender(websocket, writer)
                ])

            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            for task in pending:
                task.cancel()

            self.send_message("Attempting to reconnect to the WebSocket server...")

if __name__ == "__main__":
    def gui_message_callback(msg):
        # 您可以在此函数中将消息传递给您的前端应用程序
        pass

    bridge = LANGameLink_426_client(message_callback=gui_message_callback)
    asyncio.run(bridge.run())
