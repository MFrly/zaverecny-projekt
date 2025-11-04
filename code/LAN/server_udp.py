import socket

HOST = "0.0.0.0"
PORT = 6000

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((HOST, PORT))
    print(f"[UDP] Server naslouchá na {HOST}:{PORT} ...")
    while True:
        data, addr = s.recvfrom(1024)
        msg = data.decode("utf-8", errors="ignore").strip()
        print(f"[UDP] {addr} → {msg}")
        s.sendto(f"PONG: {msg}\n".encode("utf-8"), addr)
