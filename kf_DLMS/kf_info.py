"""
提供日志打印, 页面打印, 日志保存位置
"""

import time
import logging
import os
import io

def info(*args, **kwargs):
    """
    提供控制台打印
    :param str:
    :return:
    """
    print(*args, **kwargs)



# 日志存放目录
LOG_DIR = "Log"
os.makedirs(LOG_DIR, exist_ok=True)

timestamp = time.strftime("%Y%m%d_%H", time.localtime())
log_filename = f"{timestamp}.log"
log_path = os.path.join(LOG_DIR, log_filename)

logging.basicConfig(level=logging.INFO,
                    filename=log_path,
                    encoding='utf-8',
                    format='%(asctime)s - %(levelname)s : %(message)s')

# 全局变量：保存当前使用的 logger 和对应的小时标识
_current_logger = None
_current_hour = None


def _get_logger():
    """
    根据当前小时获取（或创建）对应的 logger。
    如果小时发生变化，则关闭旧 handler 并创建新 handler。
    """
    global _current_logger, _current_hour

    # 获取当前小时字符串，例如 "20260813_14"
    current_hour = time.strftime("%Y%m%d_%H", time.localtime())

    # 如果小时没变，直接返回已有的 logger
    if current_hour == _current_hour:
        return _current_logger

    # 小时变化了，需要重新创建 logger
    if _current_logger is not None:
        # 关闭并移除旧的所有 handler
        for handler in _current_logger.handlers[:]:
            _current_logger.removeHandler(handler)
            handler.close()

    # 创建新的 logger（名称唯一，避免干扰）
    _current_logger = logging.getLogger(f"log_info_{current_hour}")
    _current_logger.setLevel(logging.INFO)
    _current_logger.propagate = False  # 防止传播到根 logger

    # 创建文件 handler
    log_filename = f"{current_hour}.log"
    log_path = os.path.join(LOG_DIR, log_filename)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')

    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
    file_handler.setFormatter(formatter)

    # 添加到 logger
    _current_logger.addHandler(file_handler)

    # 更新当前小时
    _current_hour = current_hour

    return _current_logger


def log_info(*args, **kwargs):
    """
    将数据保存进日志
    支持 print 的所有参数（sep、end、file、flush 等）。
    """
    # 1. 在控制台打印（保持 print 的原始行为）
    # print(*args, **kwargs)

    # 2. 构造要写入日志的消息字符串
    #    注意：日志系统会自动在每条记录末尾添加换行，所以这里不包含 end
    sep = kwargs.get('sep', ' ')
    # 如果 args 为空，print 只会输出 end（默认换行），此时消息设为空字符串
    if args:
        message = sep.join(str(arg) for arg in args)
    else:
        # 若 end 不是默认换行，我们仍记录空字符串（日志会添加自己的换行）
        message = ""

    # 3. 获取当前小时的 logger 并记录日志
    logger = _get_logger()
    logger.info(message)



def log_info1(*args, **kwargs):

    # print(*args, **kwargs)

    print(*args, **kwargs)

    # 2. 捕获 print 的输出到字符串
    buffer = io.StringIO()
    print(*args, **kwargs, file=buffer)
    msg = buffer.getvalue()

    # 3. 去掉末尾的换行符（logging 会自动添加换行）
    if msg.endswith('\n'):
        msg = msg[:-1]

    # 4. 写入日志
    logging.info(msg)


def kf_info(*args, **kwargs):
    """
    在控制台和日志同时打印
    功能与 print 相同，同时将相同内容写入按小时分割的日志文件。
    支持 print 的所有参数（sep、end、file、flush 等）。
    """
    # 1. 在控制台打印（保持 print 的原始行为）
    print(*args, **kwargs)

    # 2. 构造要写入日志的消息字符串
    #    注意：日志系统会自动在每条记录末尾添加换行，所以这里不包含 end
    sep = kwargs.get('sep', ' ')
    # 如果 args 为空，print 只会输出 end（默认换行），此时消息设为空字符串
    if args:
        message = sep.join(str(arg) for arg in args)
    else:
        # 若 end 不是默认换行，我们仍记录空字符串（日志会添加自己的换行）
        message = ""

    # 3. 获取当前小时的 logger 并记录日志
    logger = _get_logger()
    logger.info(message)

# 测试
if __name__ == "__main__":
    a = 3
    b = 4
    log_info1(f"a+b = {a+b}")
    log_info1("多个", "参数", "测试", sep=" | ", end="\n")  # 自定义 sep 和 end
    log_info1("-----/-----")  # 空参数，相当于 print()









