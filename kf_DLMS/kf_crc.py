#!/usr/bin/env python3
"""
CRC‑16/X‑25 校验计算（多项式 0x1021，初始 0xFFFF，输入/输出反转，输出异或 0xFFFF）
支持短报文和嵌套长报文的校验码生成与验证。
"""

def reflect(byte: int, bits: int = 8) -> int:
    """位反转工具：将字节的 bit0 ~ bit7 翻转，如 0x80 → 0x01"""
    r = 0
    for _ in range(bits):
        r = (r << 1) | (byte & 1)
        byte >>= 1
    return r


def crc16_x25(data: bytes) -> int:
    """
    计算 CRC‑16/X‑25 校验值。
    参数: data (bytes) 待校验数据（校验码之前的所有字节）
    返回: int 16 位校验值（大端表示）
    """
    POLY   = 0x1021
    INIT   = 0xFFFF
    REFIN  = True   # 输入每个字节先位反转
    REFOUT = True   # 输出 16 位结果再位反转
    XOROUT = 0xFFFF

    crc = INIT
    for byte in data:
        b = reflect(byte) if REFIN else byte
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ POLY
            else:
                crc <<= 1
            crc &= 0xFFFF
    if REFOUT:
        crc = reflect(crc, 16)
    return crc ^ XOROUT


def format_checksum(data: bytes) -> str:
    """将校验码格式化为低字节在前的字符串，如 '0F BF'"""
    crc = crc16_x25(data)
    low = crc & 0xFF
    high = (crc >> 8) & 0xFF
    return f"{low:02X} {high:02X}"


def append_checksum(hex_str: str) -> str:
    """
    在十六进制字符串后追加校验码（低字节在前）。
    输入支持带空格或不带空格的十六进制字符串。
    """
    data = bytes.fromhex(hex_str.replace(" ", ""))
    crc = crc16_x25(data)
    return hex_str.strip() + f" {crc & 0xFF:02X} {(crc >> 8) & 0xFF:02X}"


def verify_packet(packet_hex: str) -> bool:
    """验证完整报文（最后 2 字节为小端校验码）是否正确"""
    packet_hex = packet_hex.replace(" ", "")
    if len(packet_hex) < 4:
        return False
    # 数据部分为去掉最后4个十六进制字符（2字节校验码）
    data_hex = packet_hex[:-4]
    data = bytes.fromhex(data_hex)
    # 接收到的校验码（低字节在前，转换为大端整数值）
    recv_crc_hex = packet_hex[-4:]
    recv_crc = int(recv_crc_hex[2:4] + recv_crc_hex[0:2], 16)
    calc_crc = crc16_x25(data)
    return recv_crc == calc_crc


# ==================== 测试 ====================
if __name__ == "__main__":
    # 1. 短报文测试
    print("=== 短报文 ===")
    short_hex = "A0 27 03 25 32 BF 5D E6 E6 00 C1 01 C1 00 08 01 00 63 02 00 FF 02 00 09 0C 07 EA 08 07 05 0C 3B 39 00 80 00 FF"
    print(f"数据: {short_hex} → 校验: {format_checksum(bytes.fromhex(short_hex.replace(' ', '')))}")
    print(f"完整报文: {append_checksum(short_hex)}")

    short_pkts = [
        "A0 19 03 25 32 0F BF",
        "A0 19 03 25 54 3F B9",
        "A0 19 03 25 76 2F BB",
    ]
    for pkt in short_pkts:
        print(f"验证 {pkt}: {'✔' if verify_packet(pkt) else '✘'}")

    # 2. 长报文测试（短报文 + 短校验 + 后续数据）
    print("\n=== 长报文（嵌套） ===")
    # 完整长报文，包含内层校验码
    long_packets = [
        "A0 19 03 25 32 0F BF E6 E6 00 C0 01 C1 00 03 01 00 01 08 00 FF 01 00 5A 42",
        "A0 19 03 25 54 3F B9 E6 E6 00 C0 01 C2 00 03 01 00 01 08 00 FF 01 00 E9 BC",
        "A0 19 03 25 54 3F B9 E6 E6 00 C0 01 C1 00 01 00 00 2A 00 00 FF 01 00 7A AA",
    ]
    for pkt in long_packets:
        print(f"验证 {pkt}: {'✔' if verify_packet(pkt) else '✘'}")

    # 3. 生成新的长报文示例
    print("\n=== 生成新示例 ===")
    # 示例1: 修改第五字节为 0x88，后续 C1 改为 C5
    inner_data = "A0 19 03 25 88"
    inner_crc = format_checksum(bytes.fromhex(inner_data.replace(" ", "")))
    long_without_crc = f"{inner_data} {inner_crc} E6 E6 00 C0 01 C5 00 03 01 00 01 08 00 FF 01 00"
    full_long = append_checksum(long_without_crc)
    print(f"自定义长报文: {full_long}")

    # 示例2: 另一个变体
    inner_data2 = "A0 19 03 25 AA"
    inner_crc2 = format_checksum(bytes.fromhex(inner_data2.replace(" ", "")))
    long_without_crc2 = f"{inner_data2} {inner_crc2} E6 E6 00 C0 01 C1 00 03 01 00 01 08 00 FF 01 00"
    full_long2 = append_checksum(long_without_crc2)
    print(f"自定义长报文: {full_long2}")