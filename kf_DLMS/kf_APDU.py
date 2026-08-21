from gurux_dlms import GXDLMSTranslator
from gurux_dlms.enums import TranslatorOutputType
from gurux_dlms.objects import GXDLMSData  # 可根据数据类型更换
from gurux_dlms import GXByteBuffer

def build_get_request_normal(class_id: int, obis: str, attribute_index: int) -> str:
    """
    构造 Get-Request-Normal APDU（十六进制字符串）
    :param class_id: COSEM 类 ID，例如 Data=1, Register=3, Clock=8 等
    :param obis:     逻辑名，格式 "1.0.1.4.0.255"
    :param attribute_index: 属性 ID，通常 2=值
    :return: APDU 十六进制字符串（不含 HDLC 帧）
    """
    translator = GXDLMSTranslator(TranslatorOutputType.SIMPLE_XML)
    # 构建属性描述符 XML
    xml = f"""<GetRequest>
    <GetRequestNormal>
        <InvokeIdAndPriority Value="C1" />
        <AttributeDescriptor>
            <ClassId Value="{class_id:02X}" />
            <InstanceId Value="{obis_to_hex(obis)}" />
            <AttributeId Value="{attribute_index:02X}" />
        </AttributeDescriptor>
    </GetRequestNormal>
</GetRequest>"""
    # 将 XML 转为十六进制 APDU
    pdu = translator.xmlToPdu(xml)
    # apd = GXByteBuffer.hex(pdu).upper()
    # print(f"转化后的报文:{apd}")
    # print(pdu)
    # print("转化后:", bytebuffer_to_hex(pdu))
    return bytebuffer_to_hex(pdu)
    return bytebuffer_to_hex(pdu)



def build_set_request_normal(class_id: int, obis: str, attribute_index: int,
                             value_tag: str, value_hex: str,
                             invoke_id: int = 0xC1) -> str:
    """
    生成设置一个属性的 Set-Request-Normal APDU
    :param class_id:         COSEM 类 ID (如 1 为 Data, 8 为 Clock)
    :param obis:             逻辑名，如 "0.0.1.0.0.255"
    :param attribute_index:  属性 ID，通常 2 是值
    :param value_tag:        COSEM 数据类型标签，如 "OctetString", "UInt32", "Integer" 等
    :param value_hex:        值的十六进制字符串（不含标签和长度），如 "07EA0806040B2A2FFF000000"
    :param invoke_id:        调用标识，默认 0xC1
    :return:                 APDU 十六进制字符串
    """
    obis_hex = obis_to_hex(obis)
    translator = GXDLMSTranslator(TranslatorOutputType.SIMPLE_XML)
    xml = f"""<SetRequest>
        <SetRequestNormal>
            <InvokeIdAndPriority Value="{invoke_id:02X}" />
            <AttributeDescriptor>
                <ClassId Value="{class_id:02X}" />
                <InstanceId Value="{obis_hex}" />
                <AttributeId Value="{attribute_index:02X}" />
            </AttributeDescriptor>
            <Value>
                <{value_tag} Value="{value_hex}" />
            </Value>
        </SetRequestNormal>
    </SetRequest>"""
    pdu = translator.xmlToPdu(xml)
    return bytebuffer_to_hex(pdu)

def build_set_request_list(requests: list[tuple[int, str, int, str, str]],
                           invoke_id=0xC1) -> str:
    """
    设置多个参数
    requests: [(class_id, obis, attr, value_tag, value_hex), ...]
    """
    obis_hex_func = obis_to_hex
    items_xml = ""
    for class_id, obis, attr, vtag, vhex in requests:
        obis_h = obis_hex_func(obis)
        items_xml += f"""
            <AttributeDescriptor>
                <ClassId Value="{class_id:02X}" />
                <InstanceId Value="{obis_h}" />
                <AttributeId Value="{attr:02X}" />
            </AttributeDescriptor>
            <Value>
                <{vtag} Value="{vhex}" />
            </Value>"""
    xml = f"""<SetRequest>
        <SetRequestNormalList>
            <InvokeIdAndPriority Value="{invoke_id:02X}" />
            {items_xml}
        </SetRequestNormalList>
    </SetRequest>"""
    return build_apdu_from_xml(xml)

def obis_to_hex(obis: str) -> str:
    """将 "0.0.1.0.0.255" 转为 6 字节 hex "0000010000FF" """
    parts = obis.split(".")
    return "".join(f"{int(p):02X}" for p in parts)

def build_apdu_from_xml(xml_string: str) -> str:
    """将 Gurux XML 描述转为十六进制 APDU 字符串"""
    translator = GXDLMSTranslator(TranslatorOutputType.SIMPLE_XML)
    pdu = translator.xmlToPdu(xml_string)          # 返回 GXByteBuffer
    return GXByteBuffer.hex(pdu).upper()           # 静态方法调用

def bytebuffer_to_hex(pdu, with_space=True):
    """GXByteBuffer -> 十六进制字符串（只转换有效数据）"""
    # 获取有效字节
    data = bytes(pdu.array()[:pdu.size])   # 注意这里不要加括号
    if with_space:
        return ' '.join(f"{b:02X}" for b in data)
    return data.hex().upper()

# 示例：读取当前需量（OBIS 1.0.1.4.0.255，类 ID=1，属性 2）

if __name__ == "__main__":
    apdu_hex = build_get_request_normal(class_id=8, obis="0.0.1.0.0.255", attribute_index=2)
    print(apdu_hex)  # 输出类似: C001C1 0000 0100010400FF 02
    print(type(apdu_hex))

    apdu_hex1 = build_get_request_normal(class_id=7, obis="1.0.99.2.0.255", attribute_index=4)
    print("读取负荷曲线2的当前周期",apdu_hex1)


    apdu_set_hex = build_set_request_normal(class_id=8, obis="0.0.1.0.0.255", attribute_index=2,value_tag="OctetString", value_hex="07EA0806040A173A008000FF")
    print(apdu_set_hex)

    # 设置需量周期为 15 分钟（900 秒） OBIS 1.0.1.4.0.255 的属性 3（假设）
    a = build_set_request_normal(
        class_id=1,
        obis="1.0.1.4.0.255",
        attribute_index=3,
        value_tag="UInt32",  # 32 位无符号整数
        value_hex="00000384"  # 900 的十六进制
    )
