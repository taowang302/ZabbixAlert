import SendMessages
import configlog
import readconfig
import ConfigZabbix
import ConfigSihuaMonitor

default_config={
    "SMTP": {
        "host": "smtp.126.com",
        "password": "78kxtw",
        "port": "25",
        "reveives": "tao.wang1@sihuatech.com,feng.zhang@sihuatech.com,huachun.li@sihuatech.com,baolei.han@sihuatech.com",
        "sender": "wangtao302@126.com",
        "username": "wangtao302@126.com"
    },
    "ZABBIX": {
        "password": "amsp",
        "group": "amsp",
        "user": "AMSP",
        "server": "http://172.20.222.151/zabbix/",
        "alertlevel": "1",
        "interval": "120"
    },
    "LOG": {
        "log_path": "./tickalert.log",
        "log_level": "info"
    },
    "DING": {
        "url": "https://oapi.dingtalk.com/robot/send?access_token=f4b4dc7d798a19c3543ab35e97d7ba4632e7b1bdabc6f070ce239778ff6cf12d"
    }
}

def get_config():
    config = readconfig.ReadConfig("./zabbix_monitor.conf",default_config=default_config)
    return  config.read_config()
# print(config_dic)
def get_log(log_config, log_mode=True):
    return configlog.config_log(log_config, log_mode)
# log.info("logging")
def get_zabbix(zabbix_config, log):
    # print(zabbix_config)
    return ConfigZabbix.pyzabbixAPI(zabbix_conf=zabbix_config, log=log)

def get_sendmessage(send_config, log):
    return SendMessages.SendMessages(log=log, config_dic=send_config)

def get_sihuamonitor(sihua_config,log):
    return ConfigSihuaMonitor.ConfigMonitor(sihua_config,log)

if __name__ == "__main__":
    from time import sleep
    config_dic = get_config()
    log = get_log(config_dic.get("LOG"))
    m = get_sihuamonitor(config_dic.get("SIHUA"),log)
    # m.login()
    while True:
        sihua_monitor_dic = m.getCurdata()
        if sihua_monitor_dic:
            log.info(sihua_monitor_dic)
            log.info("need to alert")
            sleep(5)