
import os
import json
import shlex

# 1. Cau hinh o dia
DISK_SIZE = 10 * 1024 * 1024
CLUSTER_SIZE = 4096
BOOT = 512
FAT_SIZE = 5120
DATA = BOOT + FAT_SIZE
TOTAL = (DISK_SIZE - DATA) // CLUSTER_SIZE

FREE = 0
EOF = 65535
RESERVED = 65534

# 2. Khoi tao o dia ao
if not os.path.exists("disk.bin") or os.path.getsize("disk.bin") != DISK_SIZE:
    with open("disk.bin", "wb") as f:
        f.truncate(DISK_SIZE)

with open("disk.bin", "r+b") as f:
    f.seek(0)
    f.write(b"OSG203 FAT FILE SYSTEM")
    f.seek(BOOT)
    f.write(RESERVED.to_bytes(2, "little"))

# 3. Doc va ghi bang FAT
def get_fat(block):
    with open("disk.bin", "rb") as f:
        f.seek(BOOT + block * 2)
        return int.from_bytes(f.read(2), "little")

def set_fat(block, value):
    with open("disk.bin", "r+b") as f:
        f.seek(BOOT + block * 2)
        f.write(value.to_bytes(2, "little"))

# 4. Quan ly thu muc
def get_files():
    with open("disk.bin", "rb") as f:
        f.seek(DATA)
        data = f.read(CLUSTER_SIZE).split(b"\0")[0]
    return json.loads(data.decode()) if data else {}

def save_files(files):
    data = json.dumps(files).encode()
    if len(data) > CLUSTER_SIZE:
        raise Exception("Thu muc da day!")
    with open("disk.bin", "r+b") as f:
        f.seek(DATA)
        f.write(data.ljust(CLUSTER_SIZE, b"\0"))

# 5. Cap phat cluster
def allocate():
    for block in range(1, TOTAL):
        if get_fat(block) == FREE:
            set_fat(block, EOF)
            return block
    return None

# 6. Giai phong chuoi cluster
def release(block):
    while block != EOF and block != FREE:
        next_block = get_fat(block)
        set_fat(block, FREE)
        block = next_block

# 7. Tao file
def create(name):
    files = get_files()

    if name in files:
        print("File da ton tai!")
        return

    if len(name.encode()) > 32:
        print("Ten file qua dai!")
        return

    files[name] = [-1, 0]
    try:
        save_files(files)
        print("Tao file thanh cong!")
    except Exception as e:
        print(e)

# 8. Ghi file
def write(name, content):
    files = get_files()

    if name not in files:
        print("Khong tim thay file!")
        return

    data = content.encode()
    blocks = []

    # Cap phat cluster moi
    for i in range(0, len(data), CLUSTER_SIZE):
        block = allocate()
        if block is None:
            for b in blocks:
                set_fat(b, FREE)
            print("Ghi file that bai!")
            return
        blocks.append(block)

    # Ghi du lieu
    try:
        with open("disk.bin", "r+b") as f:
            for i, block in enumerate(blocks):
                part = data[i * CLUSTER_SIZE:(i + 1) * CLUSTER_SIZE]
                f.seek(DATA + block * CLUSTER_SIZE)
                f.write(part.ljust(CLUSTER_SIZE, b"\0"))

        # Lien ket cac cluster
        for i in range(len(blocks) - 1):
            set_fat(blocks[i], blocks[i + 1])

        old_block = files[name][0]
        files[name] = [blocks[0] if blocks else -1, len(data)]
        save_files(files)

        # Xoa du lieu cu sau khi ghi thanh cong
        if old_block != -1:
            release(old_block)

        print("Ghi file thanh cong!")

    except Exception as e:
        if blocks:
            release(blocks[0])
        print("Ghi file that bai:", e)

# 9. Doc file
def read(name):
    files = get_files()

    if name not in files:
        print("Khong tim thay file!")
        return

    block, size = files[name]
    data = b""

    while block != -1 and block != EOF:
        with open("disk.bin", "rb") as f:
            f.seek(DATA + block * CLUSTER_SIZE)
            data += f.read(CLUSTER_SIZE)
        block = get_fat(block)

    print(data[:size].decode())

# 10. Xoa file
def delete(name):
    files = get_files()

    if name not in files:
        print("Khong tim thay file!")
        return

    block = files[name][0]
    if block != -1:
        release(block)

    del files[name]
    save_files(files)
    print("Xoa file thanh cong!")

# 11. Giao dien CLI
print("FAT FILE SYSTEM - 10 MB")
print("Lenh: create [ten_file], write [ten_file] \"noi_dung\", read [ten_file], delete [ten_file]")

while True:
    try:
        command = shlex.split(input("\nFAT> "))

        if not command:
            continue

        cmd = command[0]

        if cmd == "exit":
            break
        elif cmd == "create" and len(command) == 2:
            create(command[1])
        elif cmd == "write" and len(command) >= 3:
            write(command[1], " ".join(command[2:]))
        elif cmd == "read" and len(command) == 2:
            read(command[1])
        elif cmd == "delete" and len(command) == 2:
            delete(command[1])
        else:
            print("Lenh khong hop le!")

    except Exception as e:
        print("Loi:", e)
