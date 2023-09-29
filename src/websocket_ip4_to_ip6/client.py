import asyncio
import ssl
import websockets
import socket

class WebSocketBridge:

    SERVER_IPV6_ADDRESS = "::1"
    SERVER_PORT = 8765
    GAME_IPV4_ADDRESS = "127.0.0.1"
    GAME_TCP_PORT = 12346
    GAME_UDP_PORT = 12345

    def __init__(self):
        pass

    @staticmethod
    async def handle_websocket_errors(coro):
        async def wrapper(*args, **kwargs):
            try:
                return await coro(*args, **kwargs)
            except websockets.ConnectionClosedError:
                print("WebSocket connection lost. Attempting to reconnect...")
        return wrapper

    @handle_websocket_errors
    async def udp_receiver(self, websocket, udp_socket):
        while True:
            data = await websocket.recv()
            udp_socket.sendto(data, (self.GAME_IPV4_ADDRESS, self.GAME_UDP_PORT))

    @handle_websocket_errors
    async def udp_sender(self, websocket, udp_socket):
        while True:
            game_data, _ = udp_socket.recvfrom(4096)
            await websocket.send(game_data)

    @handle_websocket_errors
    async def tcp_receiver(self, websocket, reader):
        while True:
            data = await websocket.recv()
            reader.write(data)
            await reader.drain()

    @handle_websocket_errors
    async def tcp_sender(self, websocket, writer):
        while True:
            game_data = await writer.read(4096)
            await websocket.send(game_data)

    @handle_websocket_errors
    async def connect_to_websocket_server(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.load_verify_locations('certs/cert.pem')  # This is the server's certificate for verification
        while True:
            try:
                websocket = await websockets.connect(f"wss://[{self.IPV6_ADDRESS}]:{self.IPV6_PORT}", ssl=ssl_context)
                print("Connected to WebSocket server successfully!")
                return websocket
            except Exception as e:
                print(f"Error connecting to WebSocket server: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def run(self):
        while True:
            websocket = await self.connect_to_websocket_server()

            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.bind((self.GAME_IPV4_ADDRESS, self.GAME_UDP_PORT))

            reader, writer = await asyncio.open_connection(self.GAME_IPV4_ADDRESS, self.GAME_TCP_PORT)

            tasks = [
                self.udp_receiver(websocket, udp_socket),
                self.udp_sender(websocket, udp_socket),
                self.tcp_receiver(websocket, reader),
                self.tcp_sender(websocket, writer)
            ]

            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            for task in pending:
                task.cancel()

            udp_socket.close()
            writer.close()
            print("Attempting to reconnect to the WebSocket server...")

if __name__ == "__main__":
    bridge = WebSocketBridge()
    asyncio.run(bridge.run())
