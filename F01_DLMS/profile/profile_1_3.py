

from kf_DLMS import *
import time




def profile_1_3():
    step1 = "step1:-----------------------------------连接电表, 初始化连接参数-----------------------------------"
    step2 = "step2:-----------------------------------读取当前负荷曲线2的冻结周期和时钟-----------------------------------"
    step3 = "step3:-----------------------------------读取当前负荷曲线2的冻结上限和当前条数-----------------------------------"
    step4 = "step4:-----------------------------------根据读取的冻结上限和当前条数,循环校时至周期点前3s-----------------------------------"

    step5 = "step5:断开连接"

    # 步骤1: 连接设备
    kf_info(step1)
    conn = DLMSClient(port="COM3")
    if conn.connect():
        kf_info("连接成功")
    else:
        kf_info("连接失败")
    conn.reset_frame_type()

    # 步骤2: 读取当前负荷曲线2的冻结周期和时钟

    kf_info(step2)
    current_clock_hex = conn.read_data(8, "0.0.1.0.0.255", 2)
    current_clock = dlms_hex_to_datetime(data_analysis(current_clock_hex, "OctetString"))
    kf_info(f"电表当前时钟为:{current_clock}")

    current_cycle_hex = conn.read_data(7, "1.0.99.1.0.255", 4)
    current_cycle = data_analysis(current_cycle_hex, "UInt32") # 根据数据类型,解析报文
    current_cycle_int = int(current_cycle, 16)
    kf_info(f"电表当前冻结周期为:{current_cycle_int}")

    # 步骤3: 读取当前负荷曲线2的冻结上限
    kf_info(step3)
    profile_entries_hex = conn.read_data(7, "1.0.99.1.0.255", 8)
    profile_entries = data_analysis(profile_entries_hex, "UInt32") # 根据数据类型,解析报文
    profile_entries_int = int(profile_entries, 16)
    kf_info(f"电表当前冻结上限为:{profile_entries_int}")

    profile_entries_in_use_hex = conn.read_data(7, "1.0.99.1.0.255", 7)
    profile_entries_in_use = data_analysis(profile_entries_in_use_hex, "UInt32")
    profile_entries_in_use_int = int(profile_entries_in_use, 16)
    kf_info(f"电表当前冻结条数为:{profile_entries_in_use_int}")

    profile_add = profile_entries_in_use_int + 10


    # 步骤4: 根据读取的冻结上限和当前条数,循环校时至周期点前3s
    kf_info(step4)
    while profile_entries_in_use_int < profile_add:
        set_clock_hex = next_cycle_boundary_clock(
            original_hex=data_analysis(current_clock_hex, "OctetString"),
            cycle_seconds=current_cycle_int,
            offset_seconds=-3
        )

        kf_info(f"校时至周期点前3s的时间:{dlms_hex_to_datetime(set_clock_hex)}")
        set_clock = conn.set_data(8, "0.0.1.0.0.255", 2, "OctetString", set_clock_hex)
        if not set_clock:
            kf_info("设置失败, 表无返回值, 异常退出")
            break
        reuslt = data_analysis(set_clock, "Result")
        if reuslt == "Success":
            kf_info("时钟设置成功, 等待5s")

        time.sleep(5)

        profile_entries_hex = conn.read_data(7, "1.0.99.1.0.255", 8)
        profile_entries = data_analysis(profile_entries_hex, "UInt32")  # 根据数据类型,解析报文
        profile_entries_int = int(profile_entries, 16)
        kf_info(f"电表当前冻结上限为:{profile_entries_int}")

        profile_entries_in_use_hex = conn.read_data(7, "1.0.99.1.0.255", 7)
        profile_entries_in_use = data_analysis(profile_entries_in_use_hex, "UInt32")
        profile_entries_in_use_int = int(profile_entries_in_use, 16)
        kf_info(f"电表当前冻结条数为:{profile_entries_in_use_int}")

        current_clock_hex = conn.read_data(8, "0.0.1.0.0.255", 2)
        current_clock = dlms_hex_to_datetime(data_analysis(current_clock_hex, "OctetString"))
        kf_info(f"电表当前时钟为:{current_clock}")



    # 步骤5:断开连接
    kf_info(step5)
    conn.disconnect()


if __name__ == "__main__":

    kf_info("-----------------开始测试profile_1_3-----------------")
    profile_1_3()


