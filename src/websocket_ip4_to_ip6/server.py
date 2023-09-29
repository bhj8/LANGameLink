import asyncio
import websockets
import socket
import ssl


class LANGameLink_426_server:
    IPV6_ADDRESS = "::"
    IPV6_PORT = 8765
    GAME_IPV4_ADDRESS = "127.0.0.1"
    GAME_TCP_PORT = 24642
    GAME_UDP_PORT = 24642

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
            game_data, _ = udp_socket.recvfrom(4096)
            await websocket.send(game_data)

    @handle_websocket_errors
    async def udp_sender(self, websocket, udp_socket):
        while True:
            data = await websocket.recv()
            udp_socket.sendto(data, (self.GAME_IPV4_ADDRESS, self.GAME_UDP_PORT))

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

    async def establish_tcp_connection(self):
        while True:
            try:
                reader, writer = await asyncio.open_connection(self.GAME_IPV4_ADDRESS, self.GAME_TCP_PORT)
                print("Connected to game client successfully!")
                return reader, writer
            except ConnectionRefusedError:
                print("Failed to connect to game client. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def handle_client(self, websocket, path):
        while True:
            try:
                print(f"Client {websocket.remote_address} connected!")

                udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                reader, writer = await self.establish_tcp_connection()

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
                await writer.wait_closed()

                print(f"Client {websocket.remote_address} disconnected!")
            
            except websockets.ConnectionClosedError:
                print("WebSocket connection lost. Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)

    async def run(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain('certs/cert.pem', 'certs/private_key.pem')
        server = await websockets.serve(self.handle_client, self.IPV6_ADDRESS, self.IPV6_PORT, ssl=ssl_context)
        print(f"WebSocket server started on ws://[{self.IPV6_ADDRESS}]:{self.IPV6_PORT}")
        await server.wait_closed()


if __name__ == "__main__":
    bridge = LANGameLink_426_server()
    asyncio.run(bridge.run())
