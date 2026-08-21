"""
DLMS 客户端类
提供连接、心跳、读取、设置、断开功能
"""
import serial
import time
import sys
import xml.etree.ElementTree as ET
from typing import Optional, List
from .kf_APDU import *
from .kf_return_parsing import *
from .kf_HDLC import *
import json
import os
from .kf_info import *

class DLMSClient:
    # 预定义帧（十六进制字符串）
    FRAME_REQUEST_ID = bytes.fromhex("2F 3F 21 0D 0A")
    FRAME_BAUD_NEGOTIATE = bytes.fromhex("06 32 35 32 0D 0A")
    FRAME_HDLC_CONNECT = bytes.fromhex(
        "7E A0 20 03 25 93 1D BE 81 80 14 05 02 07 EE 06 02 07 EE 07 04 00 00 00 01 08 04 00 00 00 01 B5 D4 7E"
    )
    FRAME_AARQ = bytes.fromhex(
        "7E A0 44 03 25 10 86 E3 E6 E6 00 60 36 A1 09 06 07 60 85 74 05 08 01 01 8A 02 07 80 8B 07 60 85 74 05 08 02 01 AC 0A 80 08 30 30 30 30 30 30 30 30 BE 10 04 0E 01 00 00 00 06 5F 1F 04 00 FF FF FF 00 C8 D2 A6 7E"
    )
    FRAME_HEARTBEAT = bytes.fromhex(
        "7E A0 19 03 25 32 0F BF E6 E6 00 C0 01 C1 00 01 00 00 2A 00 00 FF 01 00 7A AA 7E"
    )

    def __init__(self, port: str = "COM3",
                 baudrate_initial: int = 300,
                 baudrate_negotiated: int = 9600,
                 timeout: float = 2.0,
                 frameType = "52",
                 frame_type_file=None):
        """
        初始化DLMS客户端
        :param port: 串口号
        :param baudrate_initial: 初始波特率（用于步骤1-2）
        :param baudrate_negotiated: 协商后波特率（用于步骤3-4及后续通信）
        :param timeout: 读超时时间（秒）
        :param frame_type_file: frame_type.json 路径, 默认None自动定位到功能模块文件夹平级目录
        """
        self.port = port
        self.baudrate_initial = baudrate_initial
        self.baudrate_negotiated = baudrate_negotiated
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        self.frameType = frameType
        self.frame_type_file = frame_type_file if frame_type_file else self._resolve_frame_type_file()
        self.frame_type = self.load_frame_type()

    def _resolve_frame_type_file(self):
        """
        自动定位 frame_type.json 的存放目录:
        放在执行脚本所在目录的上一级目录, 即与功能模块文件夹(如clock)平级.
        例如脚本在 F01_DLMS/clock/clock_1_1.py, 则生成在 F01_DLMS/frame_type.json.
        脚本直接在项目根目录时, 仍放在根目录.
        """
        main_mod = sys.modules.get("__main__")
        if main_mod and getattr(main_mod, "__file__", None):
            script_dir = os.path.dirname(os.path.abspath(main_mod.__file__))
        else:
            script_dir = os.getcwd()

        # 向上找到项目根目录(包含 pyproject.toml 或 kf_DLMS 包的目录)
        root = script_dir
        while True:
            parent = os.path.dirname(root)
            if parent == root or os.path.exists(os.path.join(root, "pyproject.toml")) or os.path.exists(os.path.join(root, "kf_DLMS")):
                break
            root = parent

        # 脚本直接在项目根目录: 文件留在根目录
        if os.path.abspath(script_dir) == os.path.abspath(root):
            return os.path.join(script_dir, "frame_type.json")
        # 否则放到脚本目录的上一级, 与功能模块文件夹平级
        return os.path.join(os.path.dirname(script_dir), "frame_type.json")

    def reset_frame_type(self):
        """将外部存储文件中的帧类型重置为 32（十六进制），并同步到实例"""
        self.frame_type = 0x32
        os.makedirs(os.path.dirname(self.frame_type_file), exist_ok=True)
        with open(self.frame_type_file, 'w') as f:
            f.write("32")
        # print("帧类型已重置为 0x32")

    def connect(self) -> bool:
        """
        执行完整的连接流程（4个步骤）
        成功返回True，失败返回False
        """
        try:
            # ---------- 步骤1：用初始波特率发送请求标识帧 ----------
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate_initial,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.SEVENBITS,
                timeout=self.timeout,
                dsrdtr=False,
                rtscts=False
            )
            kf_info(f"打开串口 {self.port} @ {self.baudrate_initial} baud")
            self.ser.rts = False
            self.ser.dtr = False

            kf_info("步骤1：发送请求标识帧")
            self._send_frame(self.FRAME_REQUEST_ID)
            response = self._read_response()
            if response:
                kf_info()
            else:
                kf_info("未收到设备回复")

            # ---------- 步骤2：发送波特率协商帧 ----------
            kf_info("步骤2：发送波特率协商帧")
            self._send_frame(self.FRAME_BAUD_NEGOTIATE)
            response = self._read_response()
            if response:
                kf_info()
            else:
                kf_info("设备未回复波特率协商，继续尝试")

            # 关闭当前串口，准备切换到新波特率
            self.ser.close()
            kf_info(f"切换波特率至 {self.baudrate_negotiated}")

            # ---------- 步骤3：用新波特率发送HDLC连接帧 ----------
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate_negotiated,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=self.timeout,
                dsrdtr=False,
                rtscts=False
            )
            kf_info("步骤3：发送HDLC连接帧")
            self._send_frame(self.FRAME_HDLC_CONNECT)
            response = self._read_response()
            if response:
                kf_info()
            else:
                kf_info("设备未回复HDLC连接帧")
                return False

            # ---------- 步骤4：发送AARQ帧 ----------
            kf_info("步骤4：发送AARQ帧")
            self._send_frame(self.FRAME_AARQ)
            response = self._read_response()
            if response:
                kf_info()
                # 这里可以检查是否为AARE确认帧，暂略
                kf_info("连接建立成功")
                return True
            else:
                kf_info("设备未回复AARQ帧")
                return False

        except serial.SerialException as e:
            kf_info(f"串口异常: {e}")
            self._close_serial()
            return False

    def heartbeat(self) -> bool:
        """
        发送心跳帧并等待响应
        成功收到响应返回True，否则False
        """
        if not self.ser or not self.ser.is_open:
            print("串口未打开，请先调用 connect()")
            return False

        kf_info("发送心跳帧")
        self._send_frame(self.FRAME_HEARTBEAT)
        response = self._read_response()
        if response:
            kf_info(f"心跳响应: {response.hex(' ').upper()}")
            return True
        else:
            kf_info("未收到心跳响应")
            return False

    def read_data(self, class_id: int, obis: str, attribute: int = 2) -> str | None:
        """
        读取数据
        :param class_id: DLMS类ID
        :param obis: OBIS码（如 "1.0.0.2.0.255"）
        :param attribute: 属性序号
        :return: 响应数据帧或None

        """
        # TODO: 根据DLMS/COSEM规范构造读取帧
        kf_info(f"读取数据: class={class_id}, obis={obis}, attr={attribute}")

        read_message = self.read_message(class_id, obis, attribute)
        data = bytes.fromhex(read_message.replace(" ", " "))
        self._send_frame(data)
        time.sleep(0.5)
        result_type = self._read_response()
        if not result_type:
            kf_info("设备没有返回数据")
            return None
        self.save_frame_type(result_type.hex(" ").upper())

        return result_type.hex(" ").upper()
        # 示例：发送一个封装好的预定义读取帧（实际开发需动态生成）
        # 这里仅打印提示
        # self._send_frame(some_frame)
        # return self._read_response()
        # raise NotImplementedError("read_data 需要根据实际协议构造帧")

    def read_data1(self, data):
        data = bytes.fromhex(data.replace(" ", " "))
        self._send_frame(data)
        time.sleep(1)
        result = self._read_response()

        if not result:
            kf_info("设备没有返回数据")
            return None
        return result

    def set_data(self,class_id: int, obis: str, attribute: int, value_tag: str, value_hex: str) -> str | None:
        """
        设置数据（示例，需根据实际协议构造帧）
        :param class_id: DLMS类ID
        :param obis: OBIS码
        :param attribute: 属性序号
        :param value_tag: 要写入的值数据类型（DLMS编码）
        :param value_hex: 要写入的值（DLMS编码）
        :return: 响应数据帧或None
        """
        # TODO: 根据DLMS/COSEM规范构造SET-REQUEST APDU


        kf_info(f"设置数据: class={class_id}, obis={obis}, attr={attribute}, value={value_hex}")


        set_message = self.set_message(class_id, obis, attribute,value_tag, value_hex)
        data = bytes.fromhex(set_message.replace(" ", " "))
        self._send_frame(data)
        time.sleep(1)
        result_byte = self._read_response()
        if not result_byte:
            kf_info("设备没有返回数据")
            return None
        self.save_frame_type(result_byte.hex(" ").upper())

        # print("接收: ",result_byte.hex(" ").upper())
        return result_byte.hex(" ").upper()
        # raise NotImplementedError("set_data 需要根据实际协议构造帧")

    def disconnect(self):
        """
        断开连接：关闭串口
        如果需要发送释放帧，可在此补充
        """
        # TODO: 可先发送RLRQ或DISC帧
        self._close_serial()
        kf_info("连接已断开")

    # ---------- 内部辅助方法 ----------
    def _send_frame(self, data: bytes):
        """发送数据帧"""
        if self.ser and self.ser.is_open:
            self.ser.write(data)
            self.ser.flush()
            kf_info(f"发送: {data.hex(' ').upper()}")
        else:
            kf_info("串口未打开，无法发送")

    def _read_response(self) -> Optional[bytes]:
        """读取所有可用响应数据，非阻塞等待timeout秒"""
        if not self.ser or not self.ser.is_open:
            return None
        time.sleep(self.timeout)  # 简单等待设备响应，可根据协议优化
        if self.ser.in_waiting > 0:
            data = self.ser.read(self.ser.in_waiting)
            kf_info(f"接收: {data.hex(" ").upper()}")
            return data
        return None

    def _close_serial(self):
        """安全关闭串口"""
        if self.ser and self.ser.is_open:
            da1 = bytes.fromhex("7E A0 07 03 25 53 63 A0 7E ".replace("",""))
            self._send_frame(da1)
            result = self._read_response()
            if result:
                kf_info("电表正常回复断开帧,串口关闭")
                self.ser.close()
            else:
                kf_info("断开帧电表没回,强制关闭串口")
                self.ser.close()

        self.ser = None

    def read_message(self,class_id: int, obis: str, attribute: int = 2):
        """
        传入obis, 类, 属性, 生成读取的完整HDLC帧
        :param class_id: 类, int类型
        :param obis: OBIS, str类型
        :param attribute: 属性,int类型
        :return: 返回完整read HDLC数据帧
        """
        frame_type = self.load_frame_type()
        apdu_str = (build_get_request_normal(class_id, obis, attribute))

        return read_build_frame(apdu_str, frame_type).hex(' ').upper()

    def set_message(self,class_id: int, obis: str, attribute: int, value_tag: str, value_hex: str):
        """
        传入数据类型数据, 组成完整的数据帧
        :param class_id:
        :param obis:
        :param attribute:
        :param value_tag: 数据类型, str类型
        :param value_hex: 数据, str类型
        :return: 返回完整set HDLC数据帧
        """
        frame_type = self.load_frame_type()
        apdu_str = (build_set_request_normal(class_id, obis, attribute, value_tag, value_hex))

        return set_build_frame(apdu_str, frame_type).hex(' ').upper()


    def load_frame_type(self):
        """从外部文件加载帧类型（纯文本十六进制），失败返回 0x32"""
        try:
            with open(self.frame_type_file, 'r') as f:
                content = f.read().strip()
                value = int(content, 16)  # 将 "32" 转为 0x32
                # print(f"从文件加载帧类型: {value:#04X}")
                return content
        except FileNotFoundError:
            kf_info("未找到有效存储文件，使用默认帧类型 0x32")
            return 0x32
        except ValueError:
            kf_info("文件内容格式错误，使用默认帧类型 0x32")
            return 0x32

    def save_frame_type(self, data:str):
        """

        :param data: str类型 传入表返回的报文, 并将报文内的frame type+2并存入json文件
        :return:
        """
        frame_data = data
        xml = parse_dlms_xml(frame_data)


        root = ET.fromstring(xml)


        for fra in root.iter("FrameType"):
            frame_type = fra.attrib["Value"]
            os.makedirs(os.path.dirname(self.frame_type_file), exist_ok=True)
            if frame_type  == "1E":
                with open(self.frame_type_file, 'w') as f:
                    f.write("10")  # 保存为 "10"
                # print(f"帧类型已更新并保存为: {self.frame_type:#04X}")
            else:
                data = (int(frame_type, 16) + 2) & 0xFF

                data_hex1 = format(data, '02X')

                with open(self.frame_type_file, 'w') as f:
                    f.write(f"{data_hex1}")  # 保存为 "34"
                # print(f"帧类型已更新并保存为: {self.frame_type:#04X}")





# ---------- 使用示例 ----------
if __name__ == "__main__":
    # client = DLMSClient(port="COM3")
    # if client.connect():
    #     # 心跳测试
    #     data = bytes.fromhex(
    #         "7E A0 19 03 25 32 0F BF E6 E6 00 C0 01 C1 00 08 00 00 01 00 00 FF 02 00 60 1A 7E".replace(" ", ""))
    #     da = client.read_data1(data)
    #     print(da)
    #
    #     # client.heartbeat()
    #
    #     # 读取/设置（需实现具体帧构造）
    #     # client.read_data(1, "1.0.0.2.0.255")
    #     # client.set_data(...)
    #
    #     client.disconnect()
    client = DLMSClient()
    # client.reset_frame_type()
    # frame = client.load_frame_type()
    # print(frame)
    # print(type(frame))

    client.reset_frame_type()

    message = client.read_message(7,"1.0.99.2.0.255", 4)
    print(message)
    data = "7E A0 18 25 03 52 B3 62 E6 E7 00 C4 01 C9 00 09 06 00 00 2A 00 00 FF E9 3E 7E"
    client.save_frame_type(data)
    frame = client.load_frame_type()
    print(frame)
    print(type(frame))
    message = client.read_message(7, "1.0.99.2.0.255", 4)
    print(message)

    set_message = client.set_message(8,"0.0.1.0.0.255", 2, "OctetString", "07EA0807050A1328008000FF")
    print(set_message)
    print(type(set_message))
