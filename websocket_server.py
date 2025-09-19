# Server WebSocket untuk Asybot (Otak Robot)
# Berjalan di Jetson Nano / PC untuk pengembangan.
# Memerlukan instalasi: pip install websockets

import asyncio
import websockets
import json

# Menyimpan koneksi klien (tablet) yang terhubung
CONNECTED_CLIENT = None

# Fungsi untuk mengirim perintah ke tablet
async def send_command(command, value):
    global CONNECTED_CLIENT
    if CONNECTED_CLIENT:
        try:
            message = json.dumps({"command": command, "value": value})
            await CONNECTED_CLIENT.send(message)
            print(f"Server > Mengirim perintah: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("Server > Koneksi ke klien terputus.")
            CONNECTED_CLIENT = None
    else:
        print("Server > Tidak ada klien yang terhubung untuk dikirimi perintah.")

# Handler utama untuk setiap koneksi yang masuk
async def handler(websocket, path):
    global CONNECTED_CLIENT
    # Hanya izinkan satu koneksi pada satu waktu
    if CONNECTED_CLIENT:
        print("Server > Menolak koneksi baru, sudah ada klien yang terhubung.")
        await websocket.close(1013, "Server sibuk")
        return
        
    CONNECTED_CLIENT = websocket
    print(f"Server > Klien (Tablet) terhubung dari {websocket.remote_address}")
    try:
        # Loop untuk mendengarkan pesan dari klien (jika ada)
        async for message in websocket:
            print(f"Server < Menerima pesan: {message}")
            # Di sini kita bisa menambahkan logika untuk memproses data dari tablet (misal: status, data sensor)
    except websockets.exceptions.ConnectionClosed:
        print("Server > Koneksi klien terputus.")
    finally:
        CONNECTED_CLIENT = None

# Fungsi untuk menjalankan simulasi perintah dari otak
async def command_simulator():
    print("Server > Simulator Perintah dimulai. Menunggu klien terhubung...")
    while True:
        # Tunggu hingga ada klien yang terhubung
        if CONNECTED_CLIENT:
            await asyncio.sleep(3)
            await send_command("setExpression", "HAPPY")
            
            await asyncio.sleep(2)
            await send_command("speak", "Halo Mori, ini adalah tes dari server WebSocket.")
            
            # Tunggu TTS selesai (estimasi)
            await asyncio.sleep(5)
            await send_command("setExpression", "NEUTRAL")
        
        await asyncio.sleep(2)


async def main():
    # Jalankan server WebSocket
    server_task = websockets.serve(handler, "localhost", 8765)
    
    # Jalankan simulator perintah secara bersamaan
    simulator_task = command_simulator()

    print("Server > Server WebSocket berjalan di ws://localhost:8765")
    await asyncio.gather(server_task, simulator_task)

if __name__ == "__main__":
    asyncio.run(main())
