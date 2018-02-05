from pyzabbix import ZabbixAPI
import requests
import traceback
import sys
import time
import datetime

class pyzabbixAPI(object):
    def __init__(self, zabbix_conf, log):
        # print("get config {}".format(zabbix_conf))
        self.prioritytostr = {'0':'ok','1':'信息','2':'警告','3':'一般严重','4':"严重","5":"灾难","R":"恢复"} #告警级别
        self.user = zabbix_conf.get("user")
        self.password = zabbix_conf.get("password")
        self.server = zabbix_conf.get("server")
        self.level = int(zabbix_conf.get("alertlevel"))
        self.alert_group = zabbix_conf.get("group").split(";")
        self.last_alert = []
        self.last_alert_dic = {}
        self.log = log
        self.zapi = self.login()
        self.recover_dic = {}

    def set_prioritytostr(self,pri_dic):
        self.prioritytostr = pri_dic

    def get_group_id(self,group):
        pass

    def login(self):
        '''''
        进行认证
        返回 api 接口
        '''
        zapi = ZabbixAPI(self.server)
        try:
            zapi.login(self.user, self.password)
        except requests.exceptions.ConnectionError as e:
            self.log.error("connect to zabbix failed")
            sys.exit()
        except:
            # log.error(traceback.print_tb(sys.exc_info()[2]))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.log.error(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            self.log.error("login fail, exit")
            sys.exit()
        else:
            self.log.info("login success")
            return zapi

    def getCurIssue(self):
        # 获取未确认的trigger
        try:
            unack_triggers = self.zapi.trigger.get(
                only_true=1,
                skipDependent=1,
                monitored=1,
                active=1,
                output='extend',
                expandDescription=1,
                selectHosts=['host'],
                withLastEventUnacknowledged=1,
                )
        except requests.exceptions.ConnectionError as e:
            self.log.error("connect to zabbix failed")
            return
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.log.error(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            return
        else:
            unack_trigger_ids = [t['triggerid'] for t in unack_triggers]
            # acked_trigger_ids = list(set(trigger_ids).difference(set(unack_trigger_ids)))
            self.log.debug("unackd ids:\{}".format(unack_trigger_ids))
            # self.log.debug("ackd ids:\{}".format(acked_trigger_ids))
            for t in unack_triggers:
                # log.info(t)
                t['unacknowledged'] = True if t['triggerid'] in unack_trigger_ids else False

            triggerdic = {}
            for t in unack_triggers:
                t['unacknowledged'] = True
                self.log.debug(t)
                group_name = self.getHostgroupName(t['hosts'][0]['host']).split(" ")
                self.log.debug("group name is {}".format(group_name))
                if int(t['value']) == 1 and t.get("unacknowledged") == True and int(t.get("priority"))> self.level and len(list(set(group_name).intersection(set(self.alert_group)))) :
                # if int(t['value']) == 1 and t.get("unacknowledged") == True and int(t.get("priority"))> self.level and len(list(set(group_name).intersection(set(self.alert_group)))) and t['hosts'][0]['host'] == "nj_solaris_rac1":
                    triggerdic[t.get("triggerid")] = {"time":time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(t['lastchange']))),
                                        "level":t['priority'],
                                        "host":t['hosts'][0]['host'],
                                        "group":group_name,
                                        "desc":t['description'],
                                        "ifknow":t['unacknowledged'],
                                        "lastvalue":self.getCurValue(t.get("triggerid"))}
            if len(triggerdic) > 0 or len(self.last_alert_dic) > 0:
                self.log.info("get {} triggers".format(len(triggerdic)))
                alert_list = [ trigger for trigger in  triggerdic ]
                cur_trigger_dic = self.identify_trigger(alert_list, triggerdic)
                self.log.info("After identify {} additional trigger warning level over than {} ".format(len(cur_trigger_dic),self.level))
                # 将本次告警数据添加到历史告警列表中
                self.last_alert_dic = dict(self.last_alert_dic,**cur_trigger_dic)
                self.last_alert = list(set(self.last_alert).union(alert_list))
                self.log.info("There are {} triggers have not recovered".format(len(self.last_alert)))
                # self.gen_msg(cur_trigger_dic)
                return cur_trigger_dic
            else:
                self.log.info("No additional warning level over than {}".format(self.level))
                return

    def identify_trigger(self,cur_alert_list,cur_trigger_dic):
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
            recover_dic[trigger_id]["lastvalue"] = self.getCurValue(trigger_id)
            recover_dic[trigger_id]["duation"] = self.getDuation(trigger_id, recover_time)
            self.last_alert.remove(trigger_id)
            del(self.last_alert_dic[trigger_id])
        # log.info("There are {} triggers have not recovered".format(len(self.last_alert)))
        self.log.info("{} trigger(s) have recovered this time".format(len(recover_list)))
        self.log.debug("recover list{}".format(recover_list))
        self.recover_dic = recover_dic
            # self.gen_msg(recover_dic,True)
        return cur_trigger_dic

    def getCurValue(self,triggerid):
        trigger_item = self.zapi.item.get(
                triggerids=triggerid,
                # hostids='14090',
                output='extend',
                sortfield="name",
                )
        return trigger_item[0].get("lastvalue")

    def getDuation(self, triggerid, recover_time):
        self.log.info(self.last_alert_dic.get(triggerid))
        occurrence_time = datetime.datetime.strptime(self.last_alert_dic.get(triggerid).get("time"),"%Y-%m-%d %H:%M:%S")
        recover_time = datetime.datetime.strptime(recover_time,"%Y-%m-%d %H:%M:%S")
        self.log.info("{} occ time:{} rec time{}".format(triggerid, occurrence_time, recover_time))
        return self.change_format(int((occurrence_time - recover_time).total_seconds()))

    def change_format(self, value):
        d = int(value / (3600*24))
        sub_d = value - d * 3600 *24
        h = int(sub_d / 3600)
        sub_h = sub_d - h * 3600
        m = int(sub_h / 60)
        sub_m = sub_h - m * 60
        s = sub_m
        return "{}天{}时{}分{}秒".format(d,h,m,s)

    def getRecorverDic(self):
        self.log.info("return recorver dic {}".format(self.recover_dic))
        return self.recover_dic

    def getHostgroupName(self,hostname):
        '''''
        通过hostname(即ip)获取host所在的监控组名
        返回由组名组成的字符串
        '''
        try:
            groups = self.zapi.host.get(
                search={"host":hostname},
                selectGroups=['name'],
                output=['groups']
                )[0]['groups']
        except requests.exceptions.ConnectionError as e:
            self.log.error("connect to zabbix failed")
            return
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.log.error(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            return
        else:
            groupname = [group['name'] for group in groups]
            return ' '.join(groupname)