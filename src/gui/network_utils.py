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
        try:
            response = requests.get("http://6.ipw.cn", timeout=10)
            response.raise_for_status()
            self.ipv6_address = response.text.strip()
        except requests.RequestException:
            self.ipv6_address = None

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

# 实例化，这样在其他模块导入时会自动执行并获取IPv6地址
network_utils_instance = NetworkUtils()

if __name__ == "__main__":
    # 测试
    import time
    time.sleep(2)  # 为了确保异步任务完成
    print(network_utils_instance.ipv6_address)
    print(network_utils_instance.available_port)
