import socket

SERVER_IP = "127.0.0.1"  # změň na IP serveru v LAN
PORT = 6000

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    print(f"[UDP] Posílám na {SERVER_IP}:{PORT}. Piš zprávy, Enter odešle, Ctrl+C ukončí.")
    while True:
        msg = input("> ")
        s.sendto((msg + "\n").encode("utf-8"), (SERVER_IP, PORT))
        data, _ = s.recvfrom(1024)
        print(data.decode("utf-8", errors="ignore").strip())
