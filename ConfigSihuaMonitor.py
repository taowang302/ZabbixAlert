import requests
import json
# import http.cookiejar
# import urllib.request
import sys
import ConfigSqlite
import time
class ConfigMonitor():
    def __init__(self, config_dic, log):
        self.install_cookies()
        self.interface_data={}
        self.base_url=config_dic.get("base_url")
        self.log = log
        self.sql = ConfigSqlite.SqliteOprate(config_dic.get("db"),log)
        self.login()
        self.recorver_dic = {}
        self.last_alert_dic = {}
        self.last_alert = []

    def install_cookies(self):
        self.cookie=dict(JSESSIONID="694707E872688C9ACA0A50401276681C")
        # print(self.cookie)

    # def login_urllib(self):
    #     headers = {"OW-Referer":"login-new","OW-Request":"PUT","X-Requested-With":"XMLHttpRequest","Content-Type":"application/json"}
    #     request = urllib.request.Request(url="http://172.31.182.133:8080/busms/rest/login", headers=headers)
    #     response = urllib.request.urlopen(request)

    def login(self):
        headers = {"OW-Referer":"login-new","OW-Request":"PUT","X-Requested-With":"XMLHttpRequest","Content-Type":"application/json"}
        ret = requests.put(cookies=self.cookie, headers=headers, url="{}/busms/rest/login".format(self.base_url),data=json.dumps({"loginName": "admin", "password": "1"}))
        if 200 == ret.status_code:
            self.log.info("login successed {}".format(ret.text))
        else:
            self.log.info("login failed {}".format(ret.status_code))

    def get_interface_data(self,currentPage, retry=0):
        # interface_data = {}
        ret = requests.get(cookies=self.cookie, url="{}/busms/rest/interfaceConfigManageService?type=ALLTYPE&cityCode=ALLCITYCODE&pageBean={}-10&_={}".format(self.base_url, currentPage,str(int(round(time.time() * 1000)))))
        return_code =  ret.status_code
        # print(return_code)
        if return_code == 200:
            response_data = json.loads(ret.text)
            total_page =  int(response_data.get("paginator").get("totalPage"))
            # print(self.interface_data)
            for per_interface in response_data.get("result"):
                self.interface_data[per_interface.get("code")] = {"name":"{}".format(per_interface.get("name")),
                                                             "delay":"{}".format(per_interface.get("delayThreshold"))}
            if currentPage == 1 and total_page > 1:
                for page in range(2,total_page+1):
                    self.get_interface_data(page)
            self.log.info("currentPage:{} total_page:{} now:{}".format(currentPage,total_page,len(self.interface_data)))
            if currentPage == total_page:
                self.log.info("now start to insert {} data".format(len(self.interface_data)))
                for code in self.interface_data:
                    self.sql.insert(name=self.interface_data.get(code).get("name"), code=code, delay=self.interface_data.get(code).get("delay"))
        else:
            print("will retry")
            if retry < 2:
                self.get_interface_data(currentPage, retry+1)

    def gen_url(self):
        url = self.base_url+"/busms/rest/DataRecordStatusService/status/"
        for code in self.sql.get_code():
            url += "".join(code)+","
        return url.rstrip(",")+"?_="+ str(int(round(time.time() * 1000)))



    def getCurdata(self):
        total_dic = {}
        cur_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        alert_dic = {}
        headers = {"OW-Request":"GET","OW-Referer":"pages/monitor/showImage"}
        ret = requests.get(headers=headers, cookies=self.cookie, url=self.gen_url())
        self.log.info(ret.status_code)
        if 200 != ret.status_code:
            sys.exit()
        response = json.loads(ret.text)
        for id in response:
            per_moni = response.get(id)
            for per_id in per_moni:
                total_dic[per_id.get("interfaceCode")] = per_id.get("delay")
                self.log.debug("{} ==> {}".format(per_id.get("interfaceName"),per_id.get("delay")))
                default_delay = self.sql.get_value(per_id.get("interfaceCode"))
                if int(per_id.get("delay")) > default_delay:
                    alert_dic[per_id.get("interfaceCode")] = {"host":per_id.get("interfaceName"),"lastvalue":per_id.get("delay"),"default":default_delay,"time":cur_time}
                    # self.log.info("alert")
        # if len(alert_dic):
        # self.log.info(alert_dic)
        alert_list = [code for code in alert_dic]
        alert_dic = self.identify(alert_list, alert_dic, total_dic)
        return alert_dic


    def identify(self,cur_alert_list, cur_trigger_dic, total_dic):
        recover_dic = {}
        recover_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        # 获取已恢复或者已知悉问题列表
        self.log.info('last alert trigger is:{} '.format(self.last_alert))
        self.log.info("cur alert trigger is {}".format(cur_alert_list))
        recover_list = list(set(self.last_alert).difference(set(cur_alert_list)))
        intersection_list = list(set(cur_alert_list).intersection(self.last_alert))
        self.log.info("intersection trigger is :{}".format(intersection_list))
        for trigger_id in intersection_list:
            del(cur_trigger_dic[trigger_id])
        self.log.info("cur trigger dic:\n{}".format(cur_trigger_dic))
        self.log.info("recorver trigger is :{}".format(recover_list))
        for trigger_id in recover_list:
            # 将已恢复的相关信息从历史问题中删除并发出通知
            recover_dic[trigger_id] = self.last_alert_dic.get(trigger_id)
            recover_dic[trigger_id]["time"] = recover_time
            recover_dic[trigger_id]["level"] = "R"
            recover_dic[trigger_id]["lastvalue"] = total_dic.get(trigger_id)
            recover_dic[trigger_id]["duation"] = self.getDuation(trigger_id, recover_time)
            self.last_alert.remove(trigger_id)
            del(self.last_alert_dic[trigger_id])
        # log.info("There are {} triggers have not recovered".format(len(self.last_alert)))
        self.log.info("{} trigger(s) have recovered this time".format(len(recover_list)))
        self.log.debug("recover list{}".format(recover_list))
        self.recover_dic = recover_dic
            # self.gen_msg(recover_dic,True)
        return cur_trigger_dic

    def getDuation(self,trigger_id,recover_time):
        pass



    def get_recorver_dic(self):
        return self.recorver_dic


if __name__ == "__main__":
    sql = ConfigSqlite.SqliteOprate("monitor.db")
    m = ConfigMonitor({"base_url":"http://172.31.182.133:8080"})
    m.login()
    # m.get_interface_data(currentPage=1)
    print(m.gen_url())
    while True:
        m.getCurdata()
        time.sleep(5)
