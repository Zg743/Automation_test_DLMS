# Automation_test_DLMS
自动化测试框架及脚本_DLMS版本


使用指南:

1. 当前已实现且直接使用的接口:

   导入方式（一条导入即可使用下列全部接口）:

       from kf_DLMS import *

   ---

   ### 一、电表通信类 DLMSClient（kf_DLMS/kf_dlms.py）

   **DLMSClient(port, baudrate_initial=300, baudrate_negotiated=9600, timeout=2.0, frameType="52", frame_type_file=None)**
   - 含义：创建 DLMS 通信客户端
   - 传参：
     - port：str，串口号，如 "COM3"
     - baudrate_initial：int，初始波特率（用于步骤1-2），默认 300
     - baudrate_negotiated：int，协商后波特率（用于步骤3-4及后续通信），默认 9600
     - timeout：float，串口读取超时（秒），默认 2.0
     - frameType：str，帧类型初始值，十六进制字符串，默认 "52"
     - frame_type_file：str 或 None，frame_type.json 路径，默认 None 自动定位到功能模块文件夹平级目录
   - 返回：客户端实例
   - 示例：`conn = DLMSClient("COM3")`

   **connect()**
   - 含义：执行完整的连接流程（4个步骤：请求标识 -> 波特率协商 -> HDLC连接 -> AARQ认证）
   - 传参：无
   - 返回：bool，True 表示连接成功
   - 注意：连接成功后必须调用 disconnect() 断开，两者成对使用

   **disconnect()**
   - 含义：发送断开帧并关闭串口
   - 传参：无
   - 返回：无

   **read_data(class_id, obis, attribute=2)**
   - 含义：读取单个 DLMS 属性值
   - 传参：
     - class_id：int，DLMS 类 ID，如 8=Clock、7=ProfileGeneric
     - obis：str，OBIS 码，如 "0.0.1.0.0.255"
     - attribute：int，属性序号，默认 2
   - 返回：str 或 None，电表应答报文（十六进制字符串），失败返回 None
   - 示例：`current_clock_hex = conn.read_data(8, "0.0.1.0.0.255", 2)`

   **set_data(class_id, obis, attribute, value_tag, value_hex)**
   - 含义：设置单个 DLMS 属性值
   - 传参：
     - class_id：int，DLMS 类 ID
     - obis：str，OBIS 码
     - attribute：int，属性序号
     - value_tag：str，COSEM 数据类型标签，如 "OctetString"、"UInt32"
     - value_hex：str，要写入的值的十六进制字符串
   - 返回：str 或 None，电表应答报文（十六进制字符串），失败返回 None
   - 示例：`conn.set_data(8, "0.0.1.0.0.255", 2, "OctetString", "07EA080705101D39008000FF")`

   **read_message(class_id, obis, attribute=2)**
   - 含义：根据传入参数生成完整的读取 HDLC 数据帧（不发送）
   - 传参：同 read_data
   - 返回：str，完整 HDLC 帧十六进制字符串

   **set_message(class_id, obis, attribute, value_tag, value_hex)**
   - 含义：根据传入参数生成完整的设置 HDLC 数据帧（不发送）
   - 传参：同 set_data
   - 返回：str，完整 HDLC 帧十六进制字符串

   **reset_frame_type()**
   - 含义：将 frame_type 重置为 0x32，并同步写入 frame_type.json
   - 传参：无
   - 返回：无

   **heartbeat()**
   - 含义：发送心跳帧并等待响应
   - 传参：无
   - 返回：bool，True 表示收到心跳响应

   典型用法（连接 -> 读写 -> 断开）:

       conn = DLMSClient("COM3")
       if conn.connect():
           current_clock_hex = conn.read_data(8, "0.0.1.0.0.255", 2)
           set_result = conn.set_data(8, "0.0.1.0.0.255", 2, "OctetString", hex_data)
       conn.disconnect()

   ---

   ### 二、时间/日期工具（kf_DLMS/kf_clock.py）

   **dlms_hex_to_datetime(hex_str)**
   - 含义：将 DLMS 12字节时钟（24位hex）转换为 datetime 对象
   - 传参：hex_str：str，DLMS 12字节 hex 字符串
   - 返回：datetime 对象
   - 示例：`dlms_hex_to_datetime("07EA080705101D39008000FF")` -> `datetime(2026, 8, 7, 16, 29, 57)`

   **datetime_to_dlms_hex(dt, hundredths=0x00, deviation=0x8000, status=0xFF)**
   - 含义：将 datetime 对象转回 DLMS 12字节 hex 字符串
   - 传参：
     - dt：datetime 对象
     - hundredths：int，百毫秒位，默认 0x00
     - deviation：int，时区偏移（分钟），默认 0x8000（未知时区）
     - status：int，时钟状态，默认 0xFF
   - 返回：str，DLMS 12字节 hex 字符串
   - 示例：`datetime_to_dlms_hex(datetime(2026, 8, 7, 16, 29, 57))` -> `"07EA080705101D39008000FF"`

   **next_cycle_boundary_clock(original_hex, cycle_seconds, offset_seconds)**
   - 含义：将 DLMS 时钟调整到下一个周期边界 + 偏移秒数（如周期 900s，偏移 -3s）
   - 传参：
     - original_hex：str，原始 DLMS 12字节时钟 hex
     - cycle_seconds：int，周期（秒），必须能被 60 整除
     - offset_seconds：int，偏移秒数，正值向后，负值向前
   - 返回：str，新的 DLMS 时钟 hex
   - 示例：`next_cycle_boundary_clock("07EA080705163B39008000FF", 900, -3)` -> `"..."`
   - 异常：cycle_seconds 不能被 60 整除时抛出 ValueError

   **next_month_boundary_clock(original_hex, offset_seconds)**
   - 含义：将 DLMS 时钟调整到当月最后一天的跨月点（下月1日 00:00:00）+ 偏移秒数
   - 传参：
     - original_hex：str，原始 DLMS 12字节时钟 hex
     - offset_seconds：int，偏移秒数，正值向过去，负值向未来
   - 返回：str，新的 DLMS 时钟 hex
   - 示例：`next_month_boundary_clock("07EA080E05101D39008000FF", -3)` -> `"...2026-08-31 23:59:57"`

   ---

   ### 三、APDU 报文构造（kf_DLMS/kf_APDU.py）

   **build_get_request_normal(class_id, obis, attribute_index)**
   - 含义：构造 Get-Request-Normal APDU（十六进制字符串）
   - 传参：
     - class_id：int，COSEM 类 ID，如 8=Clock
     - obis：str，逻辑名，如 "0.0.1.0.0.255"
     - attribute_index：int，属性 ID，通常 2=值
   - 返回：str，APDU 十六进制字符串（不含 HDLC 帧）
   - 示例：`build_get_request_normal(8, "0.0.1.0.0.255", 2)` -> `"C0 01 C1 00 08 00 00 01 00 00 FF 02 00"`

   **build_set_request_normal(class_id, obis, attribute_index, value_tag, value_hex, invoke_id=0xC1)**
   - 含义：构造 Set-Request-Normal APDU（十六进制字符串）
   - 传参：
     - class_id：int，COSEM 类 ID
     - obis：str，逻辑名
     - attribute_index：int，属性 ID
     - value_tag：str，COSEM 数据类型标签，如 "OctetString"、"UInt32"
     - value_hex：str，值的十六进制字符串
     - invoke_id：int，调用标识，默认 0xC1
   - 返回：str，APDU 十六进制字符串

   **build_set_request_list(requests, invoke_id=0xC1)**
   - 含义：构造批量设置 APDU
   - 传参：
     - requests：List[Tuple]，每个元素为 (class_id, obis, attr, value_tag, value_hex)
     - invoke_id：int，调用标识，默认 0xC1
   - 返回：str，APDU 十六进制字符串

   **obis_to_hex(obis)**
   - 含义：将点分 OBIS 码转为 6字节 hex 字符串
   - 传参：obis：str，如 "0.0.1.0.0.255"
   - 返回：str，如 "0000010000FF"

   **bytebuffer_to_hex(pdu, with_space=True)**
   - 含义：GXByteBuffer 转十六进制字符串
   - 传参：
     - pdu：GXByteBuffer 对象
     - with_space：bool，是否加空格分隔，默认 True
   - 返回：str，十六进制字符串

   ---

   ### 四、HDLC 帧构造（kf_DLMS/kf_HDLC.py）

   **read_build_frame(apdu, frame_type="32")**
   - 含义：构造读取 HDLC 帧（A0 19 03 25 开头）
   - 传参：
     - apdu：str，APDU 十六进制字符串
     - frame_type：str，控制字段，默认 "32"
   - 返回：bytes，完整 HDLC 帧（含 7E 标志和校验码）

   **set_build_frame(apdu, frame_type="32")**
   - 含义：构造设置 HDLC 帧（A0 27 03 25 开头）
   - 传参：同 read_build_frame
   - 返回：bytes，完整 HDLC 帧

   ---

   ### 五、CRC 校验（kf_DLMS/kf_crc.py）

   **crc16_x25(data)**
   - 含义：计算 CRC-16/X-25 校验值
   - 传参：data：bytes，待校验数据
   - 返回：int，16位校验值（大端表示）

   **format_checksum(data)**
   - 含义：将校验码格式化为低字节在前的字符串
   - 传参：data：bytes，待校验数据
   - 返回：str，如 "0F BF"

   **append_checksum(hex_str)**
   - 含义：在十六进制字符串后追加校验码（低字节在前）
   - 传参：hex_str：str，十六进制字符串（支持带空格或不带空格）
   - 返回：str，追加校验码后的完整字符串
   - 示例：`append_checksum("A0 19 03 25 32")` -> `"A0 19 03 25 32 0F BF"`

   **verify_packet(packet_hex)**
   - 含义：验证完整报文（最后 2 字节为小端校验码）是否正确
   - 传参：packet_hex：str，完整报文十六进制字符串
   - 返回：bool，True 表示校验通过

   ---

   ### 六、报文解析（kf_DLMS/kf_return_parsing.py）

   **parse_dlms_xml(hex_str)**
   - 含义：将电表应答报文解析为 Gurux SIMPLE_XML 格式
   - 传参：hex_str：str，电表应答报文十六进制字符串
   - 返回：str，XML 格式字符串

   **data_analysis(data, data_type)**
   - 含义：根据数据类型在原始报文中提取指定数据并返回
   - 传参：
     - data：str，电表应答原始报文
     - data_type：str，数据类型标签，如 "OctetString"、"UInt32"、"Result"
   - 返回：str，提取到的值（十六进制字符串）
   - 示例：`data_analysis(clock_hex, "OctetString")` -> 时钟 hex 字符串
   - 示例：`data_analysis(set_result_hex, "Result")` -> `"Success"` 或其他

   ---

   ### 七、打印与日志（kf_DLMS/kf_info.py）

   日志按小时分割，写入项目根目录 Log/YYYYMMDD_HH.log（固定位置，与脚本运行位置无关）。

   **info(*args, **kwargs)**
   - 含义：仅控制台打印，用法与 print 完全相同

   **log_info(*args, **kwargs)**
   - 含义：仅写入日志文件，不在控制台打印

   **log_info1(*args, **kwargs)**
   - 含义：控制台打印 + 写日志同时进行（内部方式）

   **kf_info(*args, **kwargs)**
   - 含义：控制台打印 + 写日志同时进行，测试脚本中推荐统一使用它代替 print

2. 
