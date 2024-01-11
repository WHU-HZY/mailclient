import poplib
import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QLabel, QVBoxLayout, QWidget, QTextEdit, QTabWidget, QListWidget, QHBoxLayout
from email.mime.text import MIMEText
from email.parser import Parser
from smtp_lib import send_email_via_smtp,receive_email_via_pop
import pathlib
import os
from PyQt5.QtCore import QTimer, Qt
DB_PATH = os.path.join(pathlib.Path(__file__).parent.absolute(), 'email_client.db')

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initDB()
        self.show()
        self.checkLogin()


    def checkLogin(self):
        self.cursor.execute('SELECT * FROM accounts LIMIT 1')
        account = self.cursor.fetchone()
        if account:
            print("发现保存的登录信息，正在打开邮件客户端...")
            email, password,smtp_server,pop_server = account
            self.openEmailClientWindow(email,password,smtp_server,pop_server)
        else:
            print("无保存的登录信息，显示登录界面。")

    def openEmailClientWindow(self, email, password,smtp_server,pop_server):
        self.emailClientWindow = EmailClientWindow(email, password,smtp_server,pop_server)
        self.emailClientWindow.show()
        print("正在关闭登录窗口...")
        self.close()

    def initUI(self):
        self.setWindowTitle('邮件客户端 - 登录')

        layout = QVBoxLayout()

        self.emailLabel = QLabel('邮箱地址:')
        self.emailLineEdit = QLineEdit()

        self.passwordLabel = QLabel('密码:')
        self.passwordLineEdit = QLineEdit()
        self.passwordLineEdit.setEchoMode(QLineEdit.Password)

        self.smtpLabel = QLabel('smtp_server:')
        self.smtpLineEdit = QLineEdit()

        self.popLabel = QLabel('pop_server:')
        self.popLineEdit = QLineEdit()

        self.loginButton = QPushButton('登录')
        self.loginButton.clicked.connect(self.login)

        layout.addWidget(self.emailLabel)
        layout.addWidget(self.emailLineEdit)
        layout.addWidget(self.passwordLabel)
        layout.addWidget(self.passwordLineEdit)
        layout.addWidget(self.smtpLabel)
        layout.addWidget(self.smtpLineEdit)
        layout.addWidget(self.popLabel)
        layout.addWidget(self.popLineEdit)
        layout.addWidget(self.loginButton)

        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    def initDB(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                email TEXT PRIMARY KEY,
                password TEXT,
                smtp_server TEXT,
                pop_server TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                email_id TEXT PRIMARY KEY,
                sender TEXT,
                recipient TEXT,
                subject TEXT,
                body TEXT,
                date TEXT
            )
        ''')
        self.conn.commit()

    def login(self):
        email = self.emailLineEdit.text()
        password = self.passwordLineEdit.text()
        smtp_server = self.smtpLineEdit.text()
        pop_server = self.popLineEdit.text()

        self.cursor.execute('INSERT OR REPLACE INTO accounts (email, password, smtp_server, pop_server) VALUES (?, ?, ?, ?)', (email, password, smtp_server, pop_server))
        self.conn.commit()

        self.emailClientWindow = EmailClientWindow(email, password,smtp_server,pop_server)
        self.emailClientWindow.show()
        self.close()




class EmailClientWindow(QMainWindow):
    def __init__(self, email, password, smtp_server, pop_server):
        super().__init__()
        self.email = email
        self.password = password
        self.smtp_server = smtp_server
        self.pop_server = pop_server
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refreshInbox)
        self.timer.start(30000)  # 每隔1秒触发一次timeout信号
        self.statu = 'New'
        self.label1=QLabel(self)
        self.label1.setText(self.email)
        self.label1.setGeometry(23, 1, 200, 50)

    def initUI(self):
        self.setWindowTitle('邮件客户端')
        self.setGeometry(100, 100, 800, 600)  # 设置窗口大小
        self.tabWidget = QTabWidget()

        self.createSendTab()
        self.createInboxTab()

        self.setCentralWidget(self.tabWidget)

    def createSendTab(self):
        self.sendTab = QWidget()
        layout = QVBoxLayout()

        self.recipientLabel = QLabel('收件人:')
        self.recipientLineEdit = QLineEdit()

        self.subjectLabel = QLabel('主题:')
        self.subjectLineEdit = QLineEdit()

        self.bodyTextEdit = QTextEdit()

        self.sendButton = QPushButton('发送邮件')
        self.sendButton.clicked.connect(self.sendEmail)

        layout.addWidget(self.recipientLabel)
        layout.addWidget(self.recipientLineEdit)
        layout.addWidget(self.subjectLabel)
        layout.addWidget(self.subjectLineEdit)
        layout.addWidget(self.bodyTextEdit)
        layout.addWidget(self.sendButton)

        self.sendTab.setLayout(layout)
        self.tabWidget.addTab(self.sendTab, "发送邮件")


    def createInboxTab(self):
        self.inboxTab = QWidget()
        layout = QHBoxLayout()  # 使用 QHBoxLayout

        self.mailListLayout = QVBoxLayout()  # 邮件列表的布局
        self.refreshButton = QPushButton('刷新收件箱')
        self.refreshButton.clicked.connect(self.refreshInbox)
        self.mailList = QListWidget()
        self.mailList.clicked.connect(self.displayEmailContent)
        # 把数据库中所有的邮件都显示在列表中
        saved_emails = self.cursor.execute('SELECT * FROM emails').fetchall()
        for message in saved_emails:
            self.mailList.addItem(f"Subject: {message[3]}  ,From: {message[1]}  ,Date: {message[5]}  ,Content: {message[4]}")

        self.mailListLayout.addWidget(self.refreshButton)
        self.mailListLayout.addWidget(self.mailList)

        self.mailContent = QTextEdit()  # 邮件内容展示区域
        self.mailContent.setReadOnly(True)  # 设置为只读


        layout.addLayout(self.mailListLayout, 3)  # 添加邮件列表布局
        layout.addWidget(self.mailContent, 5)  # 添加邮件内容展示区域，更大的比重

        self.inboxTab.setLayout(layout)
        self.tabWidget.addTab(self.inboxTab, "收件箱")
        # 在收件箱最下面加一行小字，显示当前登录的邮箱地址和刷新状态
        


    def displayEmailContent(self, index):
        email_id = index.row()  # 获取选中邮件的序号
        # 这里需要实现根据邮件ID获取邮件内容的逻辑
        # 假设我们有一个方法 get_email_content(email_id) 来获取邮件内容
        email_content = self.get_email_content(email_id)
        self.mailContent.setText(email_content)

    def get_email_content(self, email_id):
        # 这里应该是从服务器获取邮件内容的逻辑
        # 暂时返回假数据
        rsp = self.mailList.item(email_id).text()
        parse = rsp.split(',')
        return parse[0] + '\n' + parse[1] + '\n' + parse[2] + '\n' + parse[3] + '\n'


    def sendEmail(self):
        # 这里应该有发送邮件的逻辑，使用 self.email 和 self.password
        recipient = self.recipientLineEdit.text()
        subject = self.subjectLineEdit.text()
        body = self.bodyTextEdit.toPlainText()

        # 构建邮件内容
        msg = MIMEText(body)
        msg['From'] = self.email
        msg['To'] = recipient
        msg['Subject'] = subject

        try:
            send_email_via_smtp(self.smtp_server, 587, self.email, self.password, self.email, recipient, subject, body)
            print("邮件发送成功")
        except Exception as e:
            print("邮件发送失败:", e)
        self.recipientLineEdit.clear()
        self.subjectLineEdit.clear()
        self.bodyTextEdit.clear()

    def refreshInbox(self):
        print("refreshing inbox...")
        saved_email_ids = self.cursor.execute('SELECT email_id FROM emails').fetchall()
        try:
            pop_conn = poplib.POP3(self.pop_server)  # 更改为您的POP服务器
            pop_conn.user(self.email)
            pop_conn.pass_(self.password)

            # 获取邮件数量
            message_count, _ = pop_conn.stat()

            # 获取最新的几封邮件
            num_messages = min(255, message_count)  # 例如，获取最新的5封邮件
            for i in range(message_count, message_count - num_messages, -1):
                print(f"正在获取第{i}封邮件")
                try:
                    # 获取邮件的头部信息
                    response, lines, octets = pop_conn.top(i, 0)
                    message_content = b'\n'.join(lines).decode('utf-8')
                    message = Parser().parsestr(message_content)
                    if (message['message-id'],) in saved_email_ids:
                        break
                    print(message)
                    self.cursor.execute('INSERT INTO emails (email_id, sender, recipient, subject, body, date) VALUES (?, ?, ?, ?, ?, ?)', (message['message-id'], message['from'], message['to'], message['subject'], message.get_payload(), message['date']))
                    # self.mailList.addItem(f"Subject: {message['subject']}  ,From: {message['from']}  ,Date: {message['date']}  ,Content: {message.get_payload()}")
                    self.mailList.insertItem(0, f"Subject: {message['subject']}  ,From: {message['from']}  ,Date: {message['date']}  ,Content: {message.get_payload()}")
                except Exception as e:
                    print(f"获取邮件失败: {e}")
            self.conn.commit() # 把接收到的最新邮件保存到数据库
            pop_conn.quit() # 退出
        except Exception as e:
            print(f"邮件接收失败: {e}")


app = QApplication(sys.argv)
loginWin = LoginWindow()
sys.exit(app.exec_())
