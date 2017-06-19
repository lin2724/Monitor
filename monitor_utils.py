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
                if check_folder_is_empty(mount_path):
                    # print 'remove [%s]' % mount_path
                    os.removedirs(mount_path)
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


def run_shell(command_list):
    command = command_list
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


def set_network(device_name, cmd):
    if cmd != 'up':
        cmd = 'down'
    command = ['ifconfig', device_name, cmd]
    pipe = subprocess.Popen(args=command, stdout=subprocess.PIPE)
    while True:
        if pipe.poll() is not None:
            if cmd == 'up':
                os.system('dhclient %s' % device_name)
            if 0 != pipe.returncode:
                return False
            else:
                return True
        time.sleep(0.1)
    pass


def check_folder_is_empty(folder_path):
    #  empty folder return True
    #  not empty return False
    if not os.path.exists(folder_path):
        return False
    for root, folders, files in os.walk(folder_path):
        if len(folders) or len(files):
            return False
        return True
    return True


def rm_empty_folder(folder_path):
    if not os.path.exists(folder_path):
        return
    objects = os.listdir(folder_path)
    for object in objects:
        full_path = os.path.join(folder_path, object)
        if os.path.isdir(full_path) and check_folder_is_empty(full_path):
            os.removedirs(full_path)

















