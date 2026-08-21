from pymysql import connect
import time

from kf_DLMS import *


from gurux_dlms import GXDLMSClient, GXDLMSTranslator
from gurux_dlms.enums import Authentication, InterfaceType

# 对象类（从 objects 子包导入）
from gurux_dlms.objects import GXDLMSRegister, GXDLMSClock
# test1

step1 = "连接电表, 初始化连接参数"
step2 = "读取当前时钟和当前负荷曲线2的冻结周期"
step3 = "根据当前冻结周期, 校时至周期点前3s"
step4 = "读取当前时钟"
step5 = "断开连接"


# 步骤1: 连接设备
print(step1)
conn = DLMSClient(port="COM3")
if conn.connect():
    print("连接成功")
else:
    print("连接失败")
conn.reset_frame_type()


# 步骤2:读取当前时钟和当前负荷曲线2的冻结周期
print(step2)
current_clock_hex = conn.read_data(8,"0.0.1.0.0.255", 2)
current_clock = dlms_hex_to_datetime(data_analysis(current_clock_hex, "OctetString"))
print("电表当前时钟为:",current_clock)



current_cycle_hex = conn.read_data(7, "1.0.99.2.0.255", 4)
current_cycle = data_analysis(current_cycle_hex, "UInt32")
current_cycle_int = int(current_cycle, 16)
print("电表当前周期为:", current_cycle_int)


# 步骤3:根据当前冻结周期, 校时至周期点前3s.
print(step3)
set_clock_hex = next_cycle_boundary_clock(
    original_hex = data_analysis(current_clock_hex, "OctetString"),
    cycle_seconds= current_cycle_int,
    offset_seconds = -3
)
print("转化后的时间为:", set_clock_hex)
set_reuslt = conn.set_data(8,"0.0.1.0.0.255", 2,"OctetString", set_clock_hex)
if not set_reuslt:
    print("设置失败, 表无返回值")
reuslt = data_analysis(set_reuslt, "Result")
if reuslt == "Success":
    print("时钟设置成功, 等待5s")
else:
    print("时钟设置失败")


time.sleep(5)

# 步骤4: 读取当前时钟:
print(step4)
current_clock_hex = conn.read_data(8,"0.0.1.0.0.255", 2)
current_clock = dlms_hex_to_datetime(data_analysis(current_clock_hex, "OctetString"))


print("电表校时后时钟为:",current_clock)


# 步骤5:断开连接
print(step5)
conn.disconnect()


# 同一心跳帧重复发能回吗：
# data = "7E A0 27 03 25 32 BF 5D E6 E6 00 C1 01 C1 00 08 01 00 63 02 00 FF 02 00 09 0C 07 EA 08 07 05 0C 3B 39 00 80 00 FF FB 4D 7E"
# data2 = "7E A0 24 03 25 54 42 7E E6 E6 00 C0 03 C1 02 00 03 01 00 20 07 00 FF 03 00 00 03 01 00 20 07 00 FF 02 00 61 5F 7E"
# data3 = "7E A0 24 03 25 76 52 7C E6 E6 00 C0 03 C1 02 00 03 01 00 1F 07 00 FF 03 00 00 03 01 00 1F 07 00 FF 02 00 36 AD 7E"
# result1 = conn.read_data1(data)
# print(f"第一次接收:{result1.hex(" ").upper()}")
# time.sleep(1)
# result2 = conn.read_data1(data2)
# print(f"第二次接收:{result2.hex(" ").upper()}")
# time.sleep(1)
# result3 = conn.read_data1(data3)
# print(f"第三次接收:{result3.hex(" ").upper()}")
# time.sleep(1)
# 步骤3: 断开连接
# conn.disconnect()


