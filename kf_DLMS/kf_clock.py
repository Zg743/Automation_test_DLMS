
from datetime import datetime, timedelta

def dlms_hex_to_datetime(hex_str: str) -> datetime:
    """将 DLMS 12字节时钟（24位hex）转换为 datetime 对象"""
    data = bytes.fromhex(hex_str)
    year = int.from_bytes(data[0:2], 'big')       # 0-1 字节：年
    month = data[2]
    day = data[3]
    # 星期 data[4] 可忽略，由日期自动推导
    hour = data[5]
    minute = data[6]
    second = data[7]
    # 百毫秒 data[8] 通常 0xFF 表示未使用
    # 时区偏移 data[9:11] 为有符号16位分钟数（示例中为 0000 即 UTC 或本地）
    # 状态 data[11]
    return datetime(year, month, day, hour, minute, second)

def datetime_to_dlms_hex(dt: datetime,
                         hundredths=0x00,
                         deviation=0x8000,
                         status=0xFF) -> str:
    """将 datetime 对象转回 DLMS 12字节 hex 字符串，保留原百毫秒/偏移/状态"""
    year = dt.year.to_bytes(2, 'big')
    # 特殊处理“未知时区”保留值 0x8000
    if deviation == 0x8000:
        dev_bytes = b'\x80\x00'
    else:
        dev_bytes = deviation.to_bytes(2, 'big', signed=True)
    month = dt.month
    day = dt.day
    weekday = dt.isoweekday()  # 1=周一, 7=周日
    hour = dt.hour
    minute = dt.minute
    second = dt.second
    data = (year +
            bytes([month, day, weekday, hour, minute, second, hundredths]) +
            dev_bytes +
            bytes([status]))
    return data.hex().upper()



def next_cycle_boundary_clock(original_hex: str, cycle_seconds: int,
                              offset_seconds: int) -> str:
    """
    将 DLMS 时钟调整到：下一个周期边界 + 偏移秒数
    :param original_hex:  原始 DLMS 12 字节时钟（24 位 hex）
    :param cycle_seconds: 周期，单位秒（必须能被 60 整除，即整分钟）
    :param offset_seconds: 偏移秒数，正值向后，负值向前
    :return: 新的 DLMS 时钟 hex 串
    """

    # 1. 检查周期合法性
    if cycle_seconds % 60 != 0:
        raise ValueError("周期必须是 60 的整数倍（分钟整点）")

    # 2. 解析原始时钟
    dt = dlms_hex_to_datetime(original_hex)
    # 从原始报文中提取时区偏移和状态，保持不动
    raw_bytes = bytes.fromhex(original_hex)
    deviation = int.from_bytes(raw_bytes[9:11], 'big', signed=True)
    status = raw_bytes[11]

    # 3. 计算下一个周期边界
    # period_minutes = cycle_seconds // 60
    # print(f"下一个周期边界:{period_minutes}")
    # # 当前时间距离当天 00:00 的分钟数
    # total_minutes = dt.hour * 60 + dt.minute
    # print(f"当前时间距离当天 00:00 的分钟数:{total_minutes}")
    # # 下一个周期起始分钟数（严格大于当前时间）
    # next_block_minutes = ((total_minutes // period_minutes) + 1) * period_minutes
    # print(f"下一周期起始分钟数:{next_block_minutes}")

    # 3. 计算下一个周期边界
    period_minutes = cycle_seconds // 60
    # 当前时间距离当天 00:00 的分钟数
    total_minutes = dt.hour * 60 + dt.minute
    # 下一个周期起始分钟数（严格大于当前时间）
    next_block_minutes = ((total_minutes // period_minutes) + 1) * period_minutes

    # # 构建当天 00:00:00 作为基准
    # base_date = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    # # 下一个周期边界 datetime
    # boundary_dt = base_date + timedelta(minutes=next_block_minutes)
    #
    # # 4. 叠加偏移
    # new_dt = boundary_dt + timedelta(seconds=offset_seconds)


    # 构建当天 00:00:00 作为基准
    base_date = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    # 下一个周期边界 datetime
    boundary_dt = base_date + timedelta(minutes=next_block_minutes)
    # 4. 叠加偏移
    new_dt = boundary_dt + timedelta(seconds=offset_seconds)

    # 5. 转回 DLMS 时钟（百毫秒归零，时区/状态沿用原值）
    # return datetime_to_dlms_hex(new_dt,
    #                             hundredths=0x00,
    #                             deviation=deviation,  # 沿用原始时区
    #                             status=status)
    return datetime_to_dlms_hex(new_dt)


def next_month_boundary_clock(original_hex: str, offset_seconds: int) -> str:
    """
    将 DLMS 时钟调整到：当月最后一天的跨月点（下月1日00:00:00）+ 偏移秒数
    :param original_hex:  原始 DLMS 12 字节时钟（24 位 hex）
    :param offset_seconds: 偏移秒数，正值向过去，负值向未来
    :return: 新的 DLMS 时钟 hex 串
    """
    # 1. 解析原始时钟
    dt = dlms_hex_to_datetime(original_hex)

    # 2. 计算下月 1 号 00:00:00 作为跨月点
    if dt.month == 12:
        boundary_dt = dt.replace(year=dt.year + 1, month=1, day=1, hour=0, minute=0, second=0)
    else:
        boundary_dt = dt.replace(month=dt.month + 1, day=1, hour=0, minute=0, second=0)

    # 3. 叠加偏移
    new_dt = boundary_dt + timedelta(seconds=-offset_seconds)

    # 4. 转回 DLMS 时钟
    return datetime_to_dlms_hex(new_dt)

# ---- 使用示例 ----
if __name__ == "__main__":
    original_hex = "07EA080705163B39008000FF"


    dt = dlms_hex_to_datetime(original_hex)
    print("原始时间:", dt)  # 2026-08-06 11:42:47

    dt_hex = next_cycle_boundary_clock(original_hex, 900, -3)
    print(dt_hex)
    print(type(dt_hex))
    print("周期60s，校时至周期点前3s", dlms_hex_to_datetime(dt_hex))

    new_dt = dt + timedelta(minutes=1)
    print("加 1 分钟后:", new_dt)  # 2026-08-06 11:43:47

    # 转回 DLMS 格式（保留原百毫秒0xFF、偏移0、状态0）

    new_hex = datetime_to_dlms_hex(new_dt)
    print("新的 DLMS 时钟:", new_hex)  # 07EA0806040B2B2FFF000000

    # original_hex = "07EA0807050A1328008000FF"
    # dt = dlms_hex_to_datetime(original_hex)
    # print("原始时间:", dt)
    #
    # dt_hex = next_cycle_boundary_clock(original_hex, 3600, -3)
    # print(dt_hex)
    # print("周期60s，校时至周期点前3s", dlms_hex_to_datetime(dt_hex))

    month_dt = next_month_boundary_clock(original_hex, 90)
    print("校时至当月最后一天的hex:", month_dt)
    print("校时至当月最后一天的时间:", dlms_hex_to_datetime(month_dt))
