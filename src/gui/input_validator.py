import ipaddress

class InputValidator:

    @staticmethod
    def validate_ipv6(ip):
        try:
            ipaddress.IPv6Address(ip)
            return True
        except:
            return False

    @staticmethod
    def validate_port(port):
        try:
            port = int(port)
            return 0 <= port <= 65535
        except:
            return False

    @staticmethod
    def validate_ipv4(ip):
        try:
            ipaddress.IPv4Address(ip)
            return True
        except:
            return False
