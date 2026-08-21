

from kf_DLMS import *
import time

def profile_1_2():
    step1 = "连接电表, 初始化连接参数"
    step2 = "读取当前负荷曲线2的冻结周期"
    step3 = "读取当前负荷曲线2的冻结上限"
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

    # 步骤2: 读取当前负荷曲线2的冻结周期
    print(step2)
    current_cycle_hex = conn.read_data(7, "1.0.99.2.0.255", 4)
    current_cycle = data_analysis(current_cycle_hex, "UInt32") # 根据数据类型,解析报文
    current_cycle_int = int(current_cycle, 16)
    print("电表当前冻结周期为:", current_cycle_int)

    # 步骤3: 读取当前负荷曲线2的冻结上限
    print(step3)
    profile_entries_hex = conn.read_data(7, "1.0.99.2.0.255", 8)
    profile_entries = data_analysis(profile_entries_hex, "UInt32") # 根据数据类型,解析报文
    profile_entries_int = int(profile_entries, 16)
    print("电表当前冻结上限为:", profile_entries_int)









    # 步骤5:断开连接
    print(step5)
    conn.disconnect()


if __name__ == "__main__":
    profile_1_2()


