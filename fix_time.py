import time
import socket
import struct

def sync_time():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(2.0)
        client.sendto(b'\x1b' + 47 * b'\0', ('pool.ntp.org', 123))
        msg, _ = client.recvfrom(1024)
        t = struct.unpack('!12I', msg)[10]
        t -= 2208988800
        offset = t - time.time()
        
        if abs(offset) > 10:
            # original_time = time.time
            # time.time = lambda: original_time() + offset
            print(f"[TIME SYNC] Pyrogram uchun vaqt farqi {offset:.2f} soniya, ammo patch qilinmadi (Google API xatosi oldi olindi).")
    except Exception as e:
        print(f"[TIME SYNC] Vaqtni sinxronlashda xatolik: {e}")

sync_time()
