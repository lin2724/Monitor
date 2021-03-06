import os
import sys
import time
import threading
import signal
import subprocess
from subprocess import PIPE
import requests
import re

from monitor_utils import check_is_mount
from monitor_utils import do_mount
from monitor_utils import set_network
from monitor_utils import rm_empty_folder

gThreadMutexLog = threading.Lock()
gTerminalSig = False


class Func:
    def __init__(self):
        self.func = None
        self.timeval = 0
        self.run_cnt = 0
        self.is_init = False
        self.check_interval = 1
        pass

    def load(self, func, timeval=100):
        self.func = func
        self.timeval = timeval
        self.is_init = True
        pass

    def run(self, d_env_arg):
        global gTerminalSig
        while True:
            print 'run func...'
            ret_str = None
            try:
                ret_str = self.func()
            except:
                e = sys.exc_info()[0]
                d_env_arg['log_handle'].log(e)
            if ret_str is not None:
                d_env_arg['log_handle'].log(ret_str)
            tic_val = 1
            if self.check_interval < self.timeval:
                tic_val = self.timeval / self.check_interval
            for tic in range(1, tic_val+1):
                time.sleep(self.check_interval)
                if gTerminalSig:
                    print 'quit..'
                    return
        pass


def thread_run_func(d_env_arg=dict, c_func=Func()):
    print 'in thread func'
    if c_func.is_init:
        c_func.run(d_env_arg)
    else:
        print 'func not init!'

    pass


def sig_handle(a, b):
    global gTerminalSig
    print 'sig receive'
    gTerminalSig = True
    pass


class Log:
    def __init__(self, log_file):
        self.fd = open(log_file, 'a+')
        print 'log file %s' % log_file
        pass

    def log(self, log_str):
        cur_time_str = time.asctime()
        gThreadMutexLog.acquire()
        info = '%s  %s\n' % (cur_time_str, log_str)
        self.fd.write(info)
        self.fd.flush()
        gThreadMutexLog.release()
        pass


class Monitor:
    def __init__(self):
        self.logFile = '%s.log' % os.path.basename(__file__)
        self.logPath = '/var/log'
        self.logFilePath = os.path.join(self.logPath, self.logFile)
        self.funNodeList = list()
        signal.signal(signal.SIGINT, sig_handle)
        pass

    def run(self):
        env_arg = dict()
        log_handle = Log(log_file=self.logFilePath)
        env_arg['log_handle'] = log_handle
        task_list = list()
        for func_node in self.funNodeList:
            pro = threading.Thread(target=thread_run_func, args=(env_arg, func_node))
            pro.setDaemon(False)
            pro.start()
            task_list.append(pro)
        while True:
            time.sleep(2)
            if gTerminalSig:
                return
        pass

    def add_func(self, func, timeval):
        func_node = Func()
        func_node.load(func, timeval)
        self.funNodeList.append(func_node)
        pass


def just_test_func():
    return 'hello --'
    pass

gNetWorkFailedCnt = 0


def network_status():
    global gNetWorkFailedCnt
    test_ip = '192.168.31.1'
    test_cnt = '10'
    test_cnt_arg = '-c'
    if os.name == 'nt':
        return 'Failed'
    arg_str = ['ping', test_cnt_arg, test_cnt, test_ip]
    pipe = subprocess.Popen(args=arg_str, stderr=PIPE, stdin=PIPE, stdout=PIPE)
    buf_check = ''
    while True:
        if pipe.poll() is not None:
            if pipe.returncode != 0:
                ret_str = 'Failed to ping %s' % test_ip
                if gNetWorkFailedCnt > 3:
                    # set_network('eth0', 'down')
                    time.sleep(1)
                    # set_network('eth0', 'up')
                    gNetWorkFailedCnt = 0
                else:
                    gNetWorkFailedCnt += 1
                return ret_str
            buf_check = pipe.stdout.read()
            break
        time.sleep(0.5)

    # '4 packets transmitted, 4 received, 0% packet loss, time 3003ms'
    pattern = '(?P<packet_cnt>\d+)\s*packets transmitted,\s*(?P<packet_recv_cnt>\d+)\s*received,' \
              '\s*(?P<loss_percent>\d+)\s*% packet loss, time (?P<time_ms>\d+)ms'
    buf = '4 packets transmitted, 4 received, 0% packet loss, time 3003ms'
    m = re.search(pattern, buf_check)
    if m:
        ret_str = "trans-cnt [%s], recv-cnt [%s], loss [%s]" % \
                  (m.group('packet_cnt'), m.group('packet_recv_cnt'),
                   m.group('loss_percent'))
        if m.group('packet_cnt') == m.group('loss_percent'):
            # set_network('eth0', 'down')
            # time.sleep(1)
            # set_network('eth0', 'up')
            # return 'Reset Network for eth0'
            return 'Package loss 100%, ' + ret_str
        return ret_str
    else:
        return 'Failed to find ping result !'
    pass


def get_dev_mount_list():
    devices = os.listdir('/dev/')
    ret_list = list()
    for device in devices:
        if device[:len('sd')] == 'sd':
            ret_list.append(device)
    return ret_list
    pass

gIgnorDevList = list()


def check_ignore(dev_name):
    global gIgnorDevList
    found_flag = False
    for item in gIgnorDevList:
        if item['name'] == dev_name:
            return item['value']
    new_item = dict()
    new_item['name'] = dev_name[:]
    new_item['value'] = 0
    gIgnorDevList.append(new_item)
    return 0
    pass


def get_login_page():
    url = 'http://192.168.31.1'
    req = requests.request('GET', url, timeout=3)
    if 200 != req.status_code:
        return 'Failed to get login page'
    else:
        return 'Succeed to get login page'
    pass


def increase_ignore(dev_name):
    global gIgnorDevList
    found_flag = False
    for item in gIgnorDevList:
        if item['name'] == dev_name:
            item['value'] += 1
            return
    new_item = dict()
    new_item['name'] = dev_name[:]
    new_item['value'] = 0
    gIgnorDevList.append(new_item)
    return


def auto_mount():
    mount_dir = '/root/MountPoint'
    dev_folder = '/dev/'
    rm_empty_folder(mount_dir)
    check_dev_list = get_dev_mount_list()
    for check_dev in check_dev_list:
        if check_ignore(check_dev) > 2:
            print 'Skip ', check_dev
            continue
        print 'Check ', check_dev
        dev_path = os.path.join(dev_folder, check_dev)
        if os.path.exists(dev_path):
            if not check_is_mount(dev_path):
                mount_path = os.path.join(mount_dir, check_dev)
                if not do_mount(dev_path, mount_path):
                    increase_ignore(check_dev)
                    continue
                    # return 'Failed to mount [%s] at [%s]' % (dev_path, mount_path)
                return 'Succeed to mount [%s] at [%s]' % (dev_path, mount_path)
    return None

    pass


if __name__ == '__main__':
    monitor = Monitor()
    monitor.add_func(network_status, 60)
    monitor.add_func(auto_mount, 3)
    monitor.add_func(get_login_page, 60)

    monitor.run()
    # network_status()
    pass


