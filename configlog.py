import logging
def config_log(config, console=False):
    level_dic = {"DEBUG": logging.DEBUG,
                 "INFO": logging.INFO,
                 "ERROR": logging.ERROR,
                 "CRITICAL": logging.CRITICAL,
                 "WARNING": logging.WARNING}
    log_level = config.get("log_level","INFO")
    log_level = level_dic.get(log_level.upper())
    # log_level = log_level.upper()
    # 创建一个logger
    logger = logging.getLogger('runlog')
    logger.setLevel(log_level)
    # 定义handler的输出格式
    formatter = logging.Formatter(
        "[%(asctime)s] [%(module)s] [%(funcName)s] [%(lineno)d] %(levelname)s [TD%(thread)d] %(message)s",
        datefmt='%F %T')


    # 创建一个handler，用于输出到控制台
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        ch.setFormatter(formatter)
        # 给logger添加handler
        logger.addHandler(ch)
    else:
        # 创建一个handler，用于写入日志文件
        fh = logging.FileHandler(config.get('log_path'))
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        # 给logger添加handler
        logger.addHandler(fh)
    return logger