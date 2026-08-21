import crcmod
from .kf_crc import *

def read_build_frame(apdu: str, frame_type: str = "32") -> bytes:
    """
    构造 读取HDLC 帧
    :param apdu: 十六进制字符串，如 'C1 01 C1 00 ...'
    :param frame_type: 控制字段，十六进制字符串
    :return: 完整 HDLC 帧 bytes
    """
    # 地址（示例固定为 27 03 25，可修改）
    addr = bytes.fromhex('A0 19 03 25')

    connent_byte = bytes.fromhex('E6 E6 00')
    # 控制字段
    control = bytes([int(frame_type, 16)])   # 将字符串 "32" 转为 0x32
    # 信息字段：将字符串 APDU 转换为 bytes
    info = bytes.fromhex(apdu.replace(' ', ''))
    cs = bytes.fromhex(append_checksum((addr + control).hex(' ').upper()))
    # 组帧（不含标志和 FCS）
    frame_content = cs + connent_byte + info
    # print(frame_content.hex(' ').upper())
    # 计算 完整报文校验


    crc16 = crcmod.predefined.Crc('xmodem')
    crc16.update(frame_content)
    fcs = crc16.digest()  # 2 字节，低位在前

    # 完整帧：7E + 内容 + FCS + 7E
    return b'\x7E' + bytes.fromhex(append_checksum(frame_content.hex(' ').upper())) + b'\x7E'


def set_build_frame(apdu: str, frame_type: str = "32") -> bytes:
    """
    构造 设置HDLC 帧
    :param apdu: 十六进制字符串，如 'C1 01 C1 00 ...'
    :param frame_type: 控制字段，十六进制字符串
    :return: 完整 HDLC 帧 bytes
    """
    # 地址（示例固定为 27 03 25，可修改）
    addr = bytes.fromhex('A0 27 03 25')

    connent_byte = bytes.fromhex('E6 E6 00')
    # 控制字段
    control = bytes([int(frame_type, 16)])   # 将字符串 "32" 转为 0x32
    # 信息字段：将字符串 APDU 转换为 bytes
    info = bytes.fromhex(apdu.replace(' ', ''))
    cs = bytes.fromhex(append_checksum((addr + control).hex(' ').upper()))
    # 组帧（不含标志和 FCS）
    frame_content = cs + connent_byte + info
    # print(frame_content.hex(' ').upper())
    # 计算 完整报文校验


    crc16 = crcmod.predefined.Crc('xmodem')
    crc16.update(frame_content)
    fcs = crc16.digest()  # 2 字节，低位在前

    # 完整帧：7E + 内容 + FCS + 7E
    return b'\x7E' + bytes.fromhex(append_checksum(frame_content.hex(' ').upper())) + b'\x7E'


if __name__ == "__main__":
    apdu_hex = 'C1 01 C1 00 08 00 00 01 00 00 FF 02 00 09 0C 07 EA 08 06 04 0A 17 3A 00 80 00 FF'
    frame = read_build_frame(apdu=apdu_hex, frame_type="32")
    frame_set = set_build_frame(apdu=apdu_hex, frame_type="32")
    print(frame.hex(' ').upper())
    print(frame_set.hex(' ').upper())