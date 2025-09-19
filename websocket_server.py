# Server WebSocket untuk Asybot (Otak Robot)
# Versi 4 - Menggunakan pola modern yang kompatibel dengan websockets >= 10.x

import asyncio
import websockets
import json

# Menggunakan set untuk menyimpan koneksi klien.
# Set lebih efisien untuk menambah/menghapus dan mencegah duplikat.
CONNECTED_CLIENTS = set()

async def send_command_to_all(command, value):
    # Kirim perintah ke semua klien yang terhubung (meskipun kita hanya berharap ada satu)
    if CONNECTED_CLIENTS:
        message = json.dumps({"command": command, "value": value})
        print(f"Server > Mengirim perintah: {message}")
        # Gunakan asyncio.gather untuk mengirim ke semua klien secara bersamaan
        # Ini mencegah satu klien yang lambat menghambat yang lain
        await asyncio.gather(
            *[client.send(message) for client in CONNECTED_CLIENTS]
        )

async def handler(websocket):
    """
    Handler untuk setiap koneksi yang masuk.
    Ini adalah pola modern yang direkomendasikan.
    """
    # Tolak koneksi jika sudah ada yang terhubung.
    if len(CONNECTED_CLIENTS) >= 1:
        print(f"Server > Menolak koneksi dari {websocket.remote_address}, klien sudah ada.")
        await websocket.close(1013, "Server sibuk")
        return

    # Daftarkan koneksi baru
    CONNECTED_CLIENTS.add(websocket)
    print(f"Server > Klien (Tablet) terhubung dari {websocket.remote_address}")
    
    try:
        # Loop untuk mendengarkan pesan dari klien (jika diperlukan di masa depan)
        async for message in websocket:
            print(f"Server < Menerima pesan: {message}")
            # Logika untuk memproses pesan dari klien bisa ditambahkan di sini
    except websockets.exceptions.ConnectionClosed:
        print(f"Server > Koneksi dari {websocket.remote_address} ditutup dengan normal.")
    finally:
        # Hapus koneksi saat terputus, pastikan koneksi ada di set sebelum menghapus
        if websocket in CONNECTED_CLIENTS:
            CONNECTED_CLIENTS.remove(websocket)
        print(f"Server > Klien dari {websocket.remote_address} dihapus. Klien tersisa: {len(CONNECTED_CLIENTS)}")


async def command_simulator():
    print("Server > Simulator Perintah dimulai. Menunggu klien terhubung...")
    while True:
        # Cek setiap 2 detik apakah ada klien yang terhubung
        if CONNECTED_CLIENTS:
            await asyncio.sleep(3)
            await send_command_to_all("setExpression", "HAPPY")
            
            await asyncio.sleep(2)
            await send_command_to_all("speak", "Halo Mori, server sekarang menggunakan API modern.")
            
            # Tunggu TTS selesai (estimasi)
            await asyncio.sleep(6)
            await send_command_to_all("setExpression", "NEUTRAL")
        
        await asyncio.sleep(2)

async def main():
    # Jalankan simulator perintah sebagai background task
    asyncio.create_task(command_simulator())

    # Jalankan server menggunakan pola modern yang benar
    async with websockets.serve(handler, "localhost", 8765):
        print("Server > Server WebSocket berjalan di ws://localhost:8765")
        await asyncio.Future()  # Berjalan selamanya

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer > Server dihentikan.")

