import os
import time
import threading
import signal

gThreadMutexLog = threading.Lock()
gTerminalSig = False


class Func:
    def __init__(self):
        self.func = None
        self.timeval = 0
        self.run_cnt = 0
        self.is_init = False
        pass

    def load(self, func, timeval=100):
        self.func = func
        self.timeval = timeval
        self.is_init = True
        pass

    def run(self, d_env_arg):
        global gTerminalSig
        while True:
            if gTerminalSig:
                print 'quit..'
                return
            print 'run func...'
            ret_str = self.func()
            d_env_arg['log_handle'].log(ret_str)
            time.sleep(self.timeval)
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
        self.logFile = '%s.log' % __file__
        self.logPath = '/var/log'
        self.logFilePath = os.path.join(self.logPath, self.logFile)
        self.funNodeList = list()
        signal.signal(signal.SIGINT, sig_handle)
        pass

    def run(self):
        env_arg = dict()
        log_handle = Log(log_file=self.logFilePath)
        env_arg['log_handle'] = log_handle
        for func_node in self.funNodeList:
            pro = threading.Thread(target=thread_run_func, args=(env_arg, func_node))
            pro.setDaemon(False)
            pro.start()
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


if __name__ == '__main__':
    monitor = Monitor()
    monitor.add_func(just_test_func, 2)
    monitor.run()
    pass












































