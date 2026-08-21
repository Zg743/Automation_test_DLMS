from kf_DLMS import *
import time
import random


def clock_1_1():
    step1 = "step1:-----------------------------------连接电表, 初始化连接参数-----------------------------------"
    step2 = "step2:-----------------------------------校时至当月最后一天的跨月点前, 偏移随机300~600s, 等待随机数+30s, 循环11次-----------------------------------"
    step3 = "step3:-----------------------------------断开电表, 测试结束-----------------------------------"

    # 步骤1: 连接设备
    kf_info(step1)
    conn = DLMSClient(port="COM3")
    if conn.connect():
        kf_info("连接成功")
    else:
        kf_info("连接失败")
    conn.reset_frame_type()

    # 步骤2: 循环11次, 校时至当月最后一天的跨月点, 偏移随机数300~600s
    kf_info(step2)
    for i in range(11):
        offset = random.randint(300, 420)
        kf_info(f"第{i+1}次: 校时至跨月点前{offset}s")

        current_clock_hex = conn.read_data(8, "0.0.1.0.0.255", 2)
        current_clock = dlms_hex_to_datetime(data_analysis(current_clock_hex, "OctetString"))
        kf_info(f"电表当前时钟为:{current_clock}")

        set_clock_hex = next_month_boundary_clock(
            original_hex=data_analysis(current_clock_hex, "OctetString"),
            offset_seconds=offset
        )
        kf_info(f"校时至跨月点前{offset}s的时间:{dlms_hex_to_datetime(set_clock_hex)}")

        set_clock = conn.set_data(8, "0.0.1.0.0.255", 2, "OctetString", set_clock_hex)
        if not set_clock:
            kf_info("设置失败, 表无返回值, 异常退出")
            break
        result = data_analysis(set_clock, "Result")
        if result == "Success":
            wait_time = offset + 30
            kf_info(f"时钟设置成功, 等待{wait_time}s")
            time.sleep(wait_time)
        else:
            kf_info("时钟设置失败")

    # 步骤3: 断开电表, 测试结束
    kf_info(step3)
    conn.disconnect()


if __name__ == "__main__":

    kf_info("-----------------开始测试clock_1_1-----------------")
    clock_1_1()