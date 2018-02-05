import controlcenter
import threading
import json
# import time
from time import sleep
class myThread(threading.Thread):  # 继承父类threading.Thread
    def __init__(self, msg_mode, message, msg_nu=1, isalert=False):
        threading.Thread.__init__(self)
        self.mode = msg_mode
        self.alert_info = message
        self.msg_nu = msg_nu
        self.isalert = isalert
        self.send_message = controlcenter.get_sendmessage(config_dic, log)

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        if self.mode:
            if self.isalert:
                self.send_message.send_mail(title="共发生如下{}类告警事件,请尽快修复，或登录zabbix标记事件".format(self.msg_nu),message=self.alert_info)
            else:
                self.send_message.send_mail(title="如下{}个告警已经恢复或被人为标记已知".format(self.msg_nu),message=self.alert_info)
        else:
            if self.isalert:
                data = "### Alert on {}\n" \
                       "触发原因：{}\n\n " \
                       "告警级别：{}\n\n" \
                       "当前值：{}\n\n" \
                       "阈值：{}\n\n" \
                       "触发时间：{}".format(self.alert_info.get("host"),
                                        self.alert_info.get("desc","接口响应超出预期"),
                                        self.alert_info.get("level","严重"),
                                        self.alert_info.get("lastvalue"),
                                        self.alert_info.get("defualt"),
                                        self.alert_info.get("time"))
                self.send_message.send_ding(title="Alert On {}".format(self.alert_info.get("host")),data=data,url=zabbix_url)
            else:
                data = "### Alert on {}\n" \
                       "触发原因：{}\n\n " \
                       "告警级别：{}\n\n" \
                       "当前值：{}\n\n" \
                       "阈值：{}\n\n" \
                       "触发时间：{}".format(self.alert_info.get("host"),
                                        self.alert_info.get("desc","接口响应超出预期"),
                                        "恢复",
                                        self.alert_info.get("lastvalue"),
                                        self.alert_info.get("default"),
                                        self.alert_info.get("time"))
                self.send_message.send_ding(title="Alert On {}".format(self.alert_info.get("host")),data=data,url=zabbix_url)

def gen_msg(alertinfo, isalert=True):
    email_msg = ''
    alert_nu = len(alertinfo)
    for trr,alert_info in alertinfo.items():
        # log.debug(alert_info)
        # _thread.start_new_thread(sendmessage.send_ding, alert_info, )
        send_ding_thread = myThread(message=alert_info, msg_mode=0,isalert=isalert)
        send_ding_thread.start()
        # break
        log.info("start a new thread to send Ding message [{}]".format(send_ding_thread.ident))
        # sendmessage.send_ding(alert_info)
        per_msg = create_email_text(messages = alert_info.get("desc","接口响应超出预期"),
                                    level = prioritytostr.get(alert_info.get("level"),"严重"),
                                    alerttime = alert_info.get("time"),
                                    host = alert_info.get("host"),
                                    lastvalue=alert_info.get("lastvalue"),
                                    duation= alert_info.get("duation"),
                                    isalert= isalert)
        email_msg = email_msg + "\n ---------------------------------------------------------------\n\n" + per_msg
    if email_msg:
        log.debug("gen message down\n{}".format(email_msg))
        # sendmessage.send_mail(email_msg, alert_nu, ifalert)
        return {"message":email_msg,"msg_nu":alert_nu}
        # send_email_thread = myThread(message= email_msg, msg_nu=alert_nu, isalert=isalert, msg_mode=1)
        # send_email_thread.start()
        # log.info("start a new thread to send Email message [{}]".format(send_email_thread.ident))
        # log.info("send email end")

def create_email_text( host, messages, level, lastvalue, alerttime, duation, isalert=True):
    if isalert:
        email_message = "主机：{}\n触发原因：{}\n问题级别：{}\n当前值：{}\n问题发生时间：{}".format(host,
                                                                              messages,
                                                                              level,
                                                                              lastvalue,
                                                                              alerttime)
    else:
        email_message = "主机：{}\n触发原因：{}\n问题级别：{}\n持续时间：{}\n当前值：{}\n问题发生时间：{}".format(host,
                                                                              messages,
                                                                              level,
                                                                              duation,
                                                                              lastvalue,
                                                                              alerttime)
    return email_message

def start_sihuamonitor():
    log.info("start a new thread to run sihua monitor")
    sihua_monitor = controlcenter.get_sihuamonitor(config_dic.get("SIHUA"), log)
    while True:
        sihua_alert_dic = sihua_monitor.getCurdata()
        if sihua_alert_dic:
            gen_msg(sihua_alert_dic)
        sleep(interval)

config_dic = controlcenter.get_config()
log = controlcenter.get_log(config_dic.get("LOG"))
# log.info(config_dic)
log.info("start init...")
log.debug("laod config file done:\n{}".format(json.dumps(config_dic, indent=4, sort_keys=False, ensure_ascii=False)))
zabbix_url = config_dic.get("ZABBIX").get("server")
interval = int(config_dic.get("ZABBIX").get("interval"))
zabbix = controlcenter.get_zabbix(zabbix_config=config_dic.get("ZABBIX"), log=log)
prioritytostr = {'0':'ok','1':'信息','2':'警告','3':'一般严重','4':"严重","5":"灾难","R":"恢复"} #告警级别
zabbix.set_prioritytostr(prioritytostr)


threading._start_new_thread(start_sihuamonitor,())
#
while True:
    # cur_issue = zabbix.getCurIssue()
    # if cur_issue:
    #     msg = gen_msg(cur_issue, isalert=True)
    #     send_alertemail_thread = myThread(message= msg.get("message"), msg_nu = msg.get("msg_nu"), isalert=True, msg_mode=1)
    #     send_alertemail_thread.start()
    # recover_dic = zabbix.getRecorverDic()
    # if recover_dic:
    #     msg = gen_msg(recover_dic, isalert=False)
    #     send_recoveremail_thread = myThread(message= msg.get("message"), msg_nu = msg.get("msg_nu"), isalert=False, msg_mode=1)
    #     send_recoveremail_thread.start()
    sleep(interval)