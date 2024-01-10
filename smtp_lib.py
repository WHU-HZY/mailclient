import socket
import base64


def send_email_via_smtp(server, port, username, password, from_addr, to_addr, subject, body):
    """
    * server: SMTP 服务器地址
    * port: SMTP 服务器端口
    * username: SMTP 服务器用户名
    * password: SMTP 服务器密码
    * from_addr: 发件人地址
    * to_addr: 收件人地址
    * subject: 邮件主题
    * body: 邮件正文
    """
    message = f"From: {from_addr}\r\nTo: {to_addr}\r\nSubject: {subject}\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n{body}"   
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server, port))
        s.recv(1024)  # 读取欢迎信息
        
        # 发送 HELO 命令并读取回应
        s.sendall(b'HELO mydomain.com\r\n')
        s.recv(1024)

        # 登录
        s.sendall(b'AUTH LOGIN\r\n')
        s.recv(1024)
        s.sendall(base64.b64encode(username.encode()) + b'\r\n')
        s.recv(1024)
        s.sendall(base64.b64encode(password.encode()) + b'\r\n')
        s.recv(1024)

        # 发送邮件
        s.sendall(f'MAIL FROM: <{from_addr}>\r\n'.encode())
        s.recv(1024)
        s.sendall(f'RCPT TO: <{to_addr}>\r\n'.encode())
        s.recv(1024)
        s.sendall(b'DATA\r\n')
        s.recv(1024)
        s.sendall(f'{message}\r\n.\r\n'.encode())
        s.recv(1024)

        # 退出
        s.sendall(b'QUIT\r\n')
        s.recv(1024)


def receive_email_via_pop(server, port, username, password):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server, port))
        s.recv(1024)  # 读取欢迎信息

        # 登录
        s.sendall(f'USER {username}\r\n'.encode())
        s.recv(1024)
        s.sendall(f'PASS {password}\r\n'.encode())
        response = s.recv(1024)
        print(response)  # 打印登录响应

        # 请求邮件列表
        s.sendall(b'LIST\r\n')
        response = s.recv(1024)
        print(response)  # 打印邮件列表

        # 提取最新邮件的编号
        lines = response.splitlines()
        latest_email_number = lines[-2].split()[0]  # 假设最后一行是'.\r\n'，前一行是最新邮件的信息

        # 获取最新邮件的内容
        s.sendall(f'RETR {latest_email_number.decode()}\r\n'.encode())
        response = b""
        while True:
            part = s.recv(4096)
            response += part
            if part.endswith(b'.\r\n'):
                break

        # 假设邮件正文编码为 UTF-8
        print(response.decode('utf-8'))  # 尝试以 UTF-8 解码并打印邮件内容

        # 退出
        s.sendall(b'QUIT\r\n')
        s.recv(1024)
        return response.decode('utf-8')




