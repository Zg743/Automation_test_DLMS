from gurux_dlms import GXDLMSTranslator
from gurux_dlms.enums import TranslatorOutputType

import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from .kf_info import *
from .kf_clock import *

def parse_dlms_xml(hex_str: str) -> str:
    """

    :param hex_str: 传入原始报文, 解析为XML格式的数据
    :return: 返回xml
    """
    # 移除空格与换行
    hex_str = hex_str.replace(" ", "").replace("\n", "")
    t = GXDLMSTranslator(TranslatorOutputType.SIMPLE_XML)
    t.comments = True          # 显示注释，更容易理解
    return t.messageToXml(hex_str)



def parse_dlms_hex(xml_string: str) -> List[Dict[str, Any]]:
    """
    解析 Gurux DLMS 库输出的 SIMPLE_XML，提取所有数据对象。
    每个对象包含：逻辑名(OBIS)、值、时间戳等。
    """
    root = ET.fromstring(xml_string)
    results = []

    # 遍历所有 Structure，它们代表一个完整的数据对象
    for struct in root.iter("Structure"):
        # 第一个子元素通常是 OBIS 逻辑名
        first_child = struct.find("./*")
        if first_child is None or first_child.tag != "OctetString":
            continue

        obis_hex = first_child.attrib.get("Value", "")
        if len(obis_hex) != 12:  # 标准 OBIS 是 6 字节 → 12 个 hex 字符
            continue

        obis = ".".join(str(int(obis_hex[i:i+2], 16)) for i in range(0, 12, 2))
        obj = {"obis": obis, "attributes": {}}

        # 遍历 Structure 内的其它子元素
        children = list(struct)
        for idx, child in enumerate(children[1:], start=1):
            tag = child.tag
            val = child.attrib.get("Value", "")
            desc = f"field_{idx}"

            if tag == "OctetString" and len(val) == 24:  # 12字节日期时间
                desc = "timestamp"
            elif tag in ("UInt8", "UInt16", "UInt32", "DoubleLongUnsigned"):
                desc = "value"

            obj["attributes"][desc] = {
                "tag": tag,
                "value": val
            }

        results.append(obj)
    return results


def set_result(data):
    xml = parse_dlms_hex(data)
    print(xml)

    root = ET.fromstring(xml)

    for struct in root.iter("Result"):
        result = struct.attrib["Value"]
        if result == "Success":
            return True
        else:
            return False

def data_analysis(data, data_type):
    """
    根据传入的数据类型, 在原始报文中找到指定数据并返回
    :param data: 电表返回的原始报文
    :param data_type: 数据类型
    :return: 数据类型对应的数据
    """
    xml = parse_dlms_xml(data)
    # print(xml) #  这里需要改成日志打印xml格式数据
    log_info1(xml)

    # parse_dlms_hex(xml)
    root = ET.fromstring(xml)
    # for val in root.iter("OctetString"):
    #     dt = dlms_hex_to_datetime(val.attrib['Value'])
    #     print(f"时钟: {dt}")

    for val in root.iter(data_type):
        Value_hex = val.attrib["Value"]

    return Value_hex




if __name__ == "__main__":
    # data = "7E A0 CB 25 03 74 32 FB E6 E7 00 C4 02 CA 01 00 00 00 0B 00 81 B4 05 00 00 00 00 05 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 02 0E 09 0C 07 EA 08 0F 06 01 1E 00 00 00 00 00 12 00 00 12 00 00 12 09 4C 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 05 00 00 00 00 05 00 00 00 00 05 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 02 0E 09 0C 07 EA 08 0F 06 02 00 00 00 00 00 00 12 00 00 12 00 00 12 09 4C 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 05 00 00 00 00 05 00 00 00 00 05 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 12 51 7E"
    data = input("输入报文:")
    xml = parse_dlms_xml(data)


    print(xml)
    # parse_dlms_hex(xml)
    root = ET.fromstring(xml)
    # for val in root.iter("OctetString"):
    #     dt = dlms_hex_to_datetime(val.attrib['Value'])
    #     print(f"时钟: {dt}")

    for inv in root.iter("FrameType"):
        invoke_id = inv.attrib["Value"]

        print(f"加之前的值:{invoke_id}")
        print(type(invoke_id))
        data = int(invoke_id, 16)+2
        data_hex = data & 0xFF

        data_hex1 = format(data_hex, '02X')
        print(f"10进制+2:{data}")
        print(f"16进制+2:{data_hex1}")
        print(type(data_hex1))





