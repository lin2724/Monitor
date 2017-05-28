import os
import subprocess
from subprocess import PIPE
import re
import time


def check_is_mount(dir_path):
    if not os.path.isabs(dir_path):
        dir_path = os.path.join(os.getcwd(), dir_path)
    sh_command = ['mount']
    pipe = subprocess.Popen(args=sh_command, stderr=PIPE, stdin=PIPE, stdout=PIPE)
    check_buf = ''
    while True:
        if pipe.poll() is not None:
            if pipe.returncode != 0:
                return False
            check_buf = pipe.stdout.read()
            pattern = dir_path
            m = re.search(pattern=pattern, string=check_buf)
            if m:
                return True
            return False
        time.sleep(0.5)
    pass


def do_mount(dev_path, mount_path):
    if not os.path.exists(mount_path):
        os.system('mkdir -p %s' % mount_path)
    sh_command = ['mount', dev_path, mount_path]
    pipe = subprocess.Popen(args=sh_command)
    while True:
        if pipe.poll() is not None:
            if pipe.returncode != 0:
                return False
            return True
        time.sleep(0.5)

    pass


def check_run(program_name):
    # check if a program is running!
    # return tup (yes/no, pidlist)
    command = ['pidof', program_name]
    pipe = subprocess.Popen(args=command, stdout=subprocess.PIPE)
    while True:
        if pipe.poll() is not None:
            if 0 != pipe.returncode:
                return False, None
            else:
                ret = pipe.stdout.read()
                if ret.isdigit():
                    return True, ret.split()
                else:
                    return False, False
        time.sleep(0.1)
    pass




















