import socket

s = socket.socket()
s.bind(('localhost', 3030))

while True:
    s.listen(1)
    conn, addr = s.accept()
    

