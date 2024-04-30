import os
import time

from extra.banners import print_wonderworker
from common.coredump import CoreDump


CORE = CoreDump()


def err(cmd, msg):
    print(f'error:{msg}', cmd)


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def _help():
    print('''
    flags:
        skynet
        milkcow
        wonderworker
        buffering
        buffer-send

    commands:
        start {flag}
        kill {flag}
        restart {flag}
        ...
        help
        ls/status
        clear
        exit
''')


def status():
    CORE.read()
    print(f'''
    runtime:
 {CORE.runtime.dump()}

  skynet:       {CORE.run_sky.dump()}
  milkcow:      {CORE.run_cow.dump()}
  wonderworker: {CORE.run_wonder.dump()}

  buffering:    {CORE.should_buffer.dump()}
  buffer-send:  {CORE.send_buffer.dump()}

''')


def get_flag(cmds):
    cmd = cmds.pop(0)
    if cmd == 'MILKCOW':
        return CORE.run_cow
    elif cmd == 'SKYNET':
        return CORE.run_sky
    elif cmd == 'WONDERWORKER':
        return CORE.run_wonder
    elif cmd == 'BUFFERING':
        return CORE.should_buffer
    elif cmd == 'BUFFER-SEND':
        return CORE.send_buffer
    else:
        err(cmd, 'get_flag:flag-not-found')
    if len(cmds) > 0:
        err(cmds, 'get_flag:extra-command')


def base(cmd):
    if cmd == 'CLEAR':
        clear()
    elif cmd in ['LS', 'STATUS']:
        status()
    elif cmd == 'HELP':
        _help()
    elif cmd == 'SEND':
        CORE.send_buffer.mktrue()
    elif cmd == 'START':
        CORE.run_wonder.mktrue()
    elif cmd == 'RESTART':
        print_wonderworker()
        CORE.run_cow.mkfalse()
        CORE.run_sky.mkfalse()
        time.sleep(1)
        CORE.run_cow.mktrue()
        CORE.run_sky.mktrue()
    else:
        err(cmd, 'not-a-base-command')


def kill(cmds):
    flag = get_flag(cmds)
    if flag is not None:
        flag.mkfalse()


def start(cmds):
    flag = get_flag(cmds)
    if flag is not None:
        flag.mktrue()


def restart(cmds):
    flag = get_flag(cmds)
    if flag is not None:
        flag.mkfalse()
        time.sleep(2)
        flag.mktrue()


def get_func(cmd, cmds):
    if cmd == "KILL":
        kill(cmds)
    elif cmd == 'START':
        start(cmds)
    elif cmd == 'RESTART':
        restart(cmds)
    else:
        err(cmd, 'not-a-function')


def pass_cmds(cmd, cmds):
    if len(cmds) == 0:
        base(cmd)
    else:
        get_func(cmd, cmds)


def main():
    while True:
        cmds = input('>>> ').upper().split()
        if len(cmds) > 0:
            cmd = cmds.pop(0)
            if cmd == 'EXIT':
                break
            pass_cmds(cmd, cmds)


if __name__ in '__main__':
    print_wonderworker()
    try:
        main()
    except KeyboardInterrupt:
        print()
        print('bye')
