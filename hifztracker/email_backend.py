import smtplib
import socket
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend

class SMTP_IPv4(smtplib.SMTP):
    def connect(self, host='localhost', port=0):
        if host.startswith('['):
            return super().connect(host, port)
        
        try:
            # Resolve to IPv4 (AF_INET)
            addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
            if addr_info:
                # Use the first IPv4 address
                target_ip = addr_info[0][4][0]
                # Connect to the IP
                code, msg = super().connect(target_ip, port)
                # Restore the original hostname for SSL/TLS verification
                self._host = host
                return code, msg
        except Exception:
            pass
            
        return super().connect(host, port)

class EmailBackend(DjangoEmailBackend):
    @property
    def connection_class(self):
        return SMTP_IPv4
