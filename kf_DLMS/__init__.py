"""
DLMS 电表通信自动化测试框架
作者: 周杨
用法:
    from kf_DLMS import DLMSClient
    from kf_DLMS import parse_dlms_xml, data_analysis
    from kf_DLMS import next_cycle_boundary_clock, dlms_hex_to_datetime
"""
__version__ = "0.1.0"

from .kf_crc import *
from .kf_clock import *
from .kf_info import *
from .kf_APDU import *
from .kf_HDLC import *
from .kf_return_parsing import *
from .kf_dlms import DLMSClient

__all__ = [
    # kf_crc
    "crc16_x25", "format_checksum", "append_checksum", "verify_packet",
    # kf_clock
    "dlms_hex_to_datetime", "datetime_to_dlms_hex", "next_cycle_boundary_clock",
    "next_month_boundary_clock",
    # kf_info
    "info", "log_info", "log_info1", "kf_info",
    # kf_APDU
    "build_get_request_normal", "build_set_request_normal",
    "build_set_request_list", "obis_to_hex", "build_apdu_from_xml", "bytebuffer_to_hex",
    # kf_HDLC
    "read_build_frame", "set_build_frame",
    # kf_return_parsing
    "parse_dlms_xml", "parse_dlms_hex", "data_analysis",
    # kf_dlms
    "DLMSClient",
]