#!/usr/bin/env python

import argparse
import os
import select
from datetime import datetime

from fanotify import fanotify

os.AT_FDCWD    = getattr(os, "AT_FDCWD",    -100)
os.O_LARGEFILE = getattr(os, "O_LARGEFILE", 0x00008000)
os.O_CLOEXEC   = getattr(os, "O_CLOEXEC",   0x00080000)

def call(func, *args):
    try:
        return func(*args)
    except:
        pass

def readall(path):
    with open(path, "r") as f:
        return f.read().rstrip()

def pretty(obj):
    if type(obj) is datetime:
        return obj.strftime("%Y-%m-%d %H:%M:%S.%f")

    return str(obj)

def mountpoint(path):
    parent = os.path.dirname(path)

    if os.path.ismount(path):
        return path
    elif parent != path:
        return mountpoint(parent)

    return "?"

def handle(notify):
    event = notify.read()
    when = pretty(datetime.now())

    # always allow
    if event.mask & (fanotify.OPEN_PERM | fanotify.ACCESS_PERM):
        notify.reply(event, fanotify.ALLOW)

    who = call(readall, "/proc/{}/comm".format(event.pid)) or "?"
    what = call(os.readlink, "/proc/self/fd/{}".format(event.fd)) or "?"
    want = fanotify.describe(event.mask)

    print("[{}] {}({}) | ({}) | {}".format(pretty(when), who, event.pid, want, what))

    event.close()

def main():
    parser = argparse.ArgumentParser(prog="fanotify")
    parser.add_argument("path", help="path to monitor", nargs=1)

    args = parser.parse_args()
    args.path = "".join(args.path)

    print("path: '{}' (mountpoint: '{}')".format(args.path, mountpoint(args.path)))

    notify = fanotify.Fanotify()
    notify.init(fanotify.CLASS_CONTENT | fanotify.CLOEXEC | fanotify.NONBLOCK,
                os.O_CLOEXEC | os.O_LARGEFILE)
    notify.mark(fanotify.MARK_ADD | fanotify.MARK_MOUNT,
                fanotify.OPEN_PERM | fanotify.CLOSE_WRITE | fanotify.CLOSE_NOWRITE,
                os.AT_FDCWD,
                args.path.encode("utf-8"))

    poller = select.poll()
    poller.register(notify.fileno(), select.POLLIN | select.POLLERR)

    while True:
        for _, events in poller.poll(1000):
            if events & select.POLLERR:
                print("something went wrong")
            elif events & select.POLLIN:
                handle(notify)

    notify.close()

if __name__ ==  "__main__":
    main()
