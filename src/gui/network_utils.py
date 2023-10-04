import socket
import requests
import threading

class NetworkUtils:
    def __init__(self):
        self.ipv6_address = "自动获取中..."
        self.available_port = self.find_available_port()

        # 启动线程来获取IPv6地址
        threading.Thread(target=self._update_ipv6_address, daemon=True).start()

    def _update_ipv6_address(self):
        """
        使用外部服务获取公网IPv6地址
        """
        count = 0
        while count <5:
            try:
                response = requests.get("http://6.ipw.cn", timeout=3)
                response.raise_for_status()
                self.ipv6_address = response.text.strip()
                return
            except requests.RequestException:
                continue
            finally :
                count += 1

    @staticmethod
    def find_available_port(start=20000, end=60000):
        """
        在指定的范围内查找可用的端口
        """
        for port in range(start, end + 1):
            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("::1", port))
                    return port
                except socket.error:
                    continue
        raise ValueError("No available port found in the given range!")
    @staticmethod
    def get_local_ipv4_address():
        """
        获取本地IPv4地址。使用UDP连接外部地址的方法来确定内网地址。
        """
        try:
            # 注意: 这并不会真的连接到远程地址，它只是使用系统来获取最合适的网络接口的IP地址
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("114.114.114.114", 80))  # 使用Google的公共DNS服务器地址
                return s.getsockname()[0]
        except socket.error:
            return "无法获取IPv4地址"

# 实例化，这样在其他模块导入时会自动执行并获取IPv6地址
network_utils_instance = NetworkUtils()

if __name__ == "__main__":
    # 测试
    import time
    time.sleep(2)  # 为了确保异步任务完成
    print(network_utils_instance.ipv6_address)
    print(network_utils_instance.available_port)
    print(network_utils_instance.get_local_ipv4_address())  # 打印本地IPv4地址
