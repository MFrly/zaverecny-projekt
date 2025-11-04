import socket

SERVER_IP = "127.0.0.1"  # pokud se připojuješ z jiného PC v LAN, dej sem IP serveru
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((SERVER_IP, PORT))
    print(f"[TCP] Připojeno k {SERVER_IP}:{PORT}. Piš zprávy, Enter odešle, Ctrl+C ukončí.")
    while True:
        msg = input("> ")
        s.sendall((msg + "\n").encode("utf-8"))
        data = s.recv(1024)
        print(data.decode("utf-8", errors="ignore").strip())
