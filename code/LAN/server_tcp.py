import socket

HOST = "0.0.0.0"   # naslouchat na všech rozhraních (lokálně i v síti)
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"[TCP] Server naslouchá na {HOST}:{PORT} ...")
    conn, addr = s.accept()
    with conn:
        print(f"[TCP] Připojeno:", addr)
        while True:
            data = conn.recv(1024)
            if not data:
                print("[TCP] Klient se odpojil.")
                break
            msg = data.decode("utf-8", errors="ignore").strip()
            print(f"[TCP] Přijato: {msg}")
            conn.sendall(f"ECHO: {msg}\n".encode("utf-8"))
