import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import json
import traceback
import requests
import sys

class SendMessages():
    def __init__(self, log, config_dic):
        self.log =log
        self.dingtalkurl = config_dic.get("DING").get("url")
        self.sender = config_dic.get("SMTP").get("sender")
        self.port = config_dic.get("SMTP").get("port")
        self.host = config_dic.get("SMTP").get("host")
        self.username = config_dic.get("SMTP").get("username")
        self.password = config_dic.get("SMTP").get("password")
        self.reveives = config_dic.get("SMTP").get("reveives")
        self.dingmsg = {"actionCard": {"title": "",
                                       "text": "",
                                       "hideAvatar": "0",
                                       "btnOrientation": "0",
                                       "btns": [{"title": "详情",
                                                 "actionURL": "" }]},
                        "msgtype": "actionCard"}

    def send_ding(self, title, data, url):
        # self.log.info(data)
        self.dingmsg["actionCard"]["title"] = title
        self.dingmsg["actionCard"]["text"] = data
        self.dingmsg["actionCard"]["btns"][0]["actionURL"] = url
        self.log.info("Send Ding message:\n{}".format(json.dumps(self.dingmsg, indent=4, sort_keys=False, ensure_ascii=False)))
        url = self.dingtalkurl
        try:
            ret = requests.post(url, data=json.dumps(self.dingmsg), headers = {"Content-Type": "application/json"})
        except requests.exceptions.ConnectionError as e:
            self.log.error("connect to Ding failed")
            return 0
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.log.error("found error when send Ding messages")
            self.log.error(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            return 0
        else:
            # self.log.debug("Get receive{}".format(ret.text))
            resp = json.loads(ret.text)
            status_code = ret.status_code
            if 200 == status_code:
                self.log.debug("receive response:\n".format(json.dumps(resp, indent=4, sort_keys=False, ensure_ascii=False)))
                if 0 == resp.get("errcode"):
                    self.log.info("get response errcode is 0, so send Ding successed")
                    return 1
                else:
                    self.log.error("Get receive{}".format(json.dumps(resp, indent=4, sort_keys=False, ensure_ascii=False)))
                    self.log.error("get response errcode is not 0, send Ding failed")
                    return 0
            else:
                self.log.error("return code:{} is not 200".format(status_code))
                self.log.error("get response:{}".format(resp))
                return 0


    def send_mail(self, title, message):
        email_message = title + message
        self.log.debug("email message\n{}".format(email_message))
        self.log.debug(type(self.reveives))
        receivers = (self.reveives.split(","))  # 接收邮件
        message = MIMEText(str(email_message), 'plain', 'utf-8')
        self.log.debug(str(receivers))
        self.log.debug('type => {}\n message =>{}'.format(type(message), message))
        message['From'] = formataddr(["ZABBIX Alert", self.username])
        message['To'] = ",".join(receivers)
        subject = "Zabbix Alert"
        message['Subject'] = Header(subject, 'utf-8')
        self.log.debug(message.as_string())
        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(self.host, 25)  # 25 为 SMTP 端口号
            smtpObj.login(self.username, self.password)
            smtpObj.sendmail(self.username, receivers, message.as_string())
        except smtplib.SMTPException as e:
            self.log.error("Send email fail,{}".format(e))
            return 0
            # raise AttributeError(e) from e
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.log.error("send Email message failed")
            self.log.error(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            # log.error(sys.exc_info()[1])
            return 0
        else:
            self.log.info("Send email success")
            return 1