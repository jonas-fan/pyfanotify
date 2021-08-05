import ctypes
import errno
import os

libc = ctypes.CDLL(None, use_errno=True)

"""Flags used for `fanotify_init()`."""
CLASS_NOTIF       = 0x00000000
CLASS_CONTENT     = 0x00000004
CLASS_PRE_CONTENT = 0x00000008
CLOEXEC           = 0x00000001
NONBLOCK          = 0x00000002
UNLIMITED_QUEUE   = 0x00000010
UNLIMITED_MARKS   = 0x00000020

"""Flags used for `fanotify_mark()`."""
MARK_ADD                 = 0x00000001
MARK_REMOVE              = 0x00000002
MARK_DONT_FOLLOW         = 0x00000004
MARK_ONLYDIR             = 0x00000008
MARK_MOUNT               = 0x00000010
MARK_IGNORED_MASK        = 0x00000020
MARK_IGNORED_SURV_MODIFY = 0x00000040
MARK_FLUSH               = 0x00000080

"""Events that user-space can register for."""
ACCESS         = 0x00000001
MODIFY         = 0x00000002
CLOSE_WRITE    = 0x00000008
CLOSE_NOWRITE  = 0x00000010
OPEN           = 0x00000020
Q_OVERFLOW     = 0x00004000
OPEN_PERM      = 0x00010000
ACCESS_PERM    = 0x00020000
ONDIR          = 0x40000000
EVENT_ON_CHILD = 0x08000000

"""Reponses for `*_PERM` events."""
ALLOW = 0x01
DENY  = 0x02

def panic_on(condition, message=""):
    if condition:
        raise AssertionError(message)

class cstructure(ctypes.Structure):
    """Base class of ctypes strcuture."""

    def reference(self):
        """Return the memory address of this instnace.

        E.g., `(void *)&object` in C.

        Returns:
            int: Memory address.
        """
        return ctypes.byref(self)

    def size(self):
        """Return the size of this instance.

        Returns:
            int: Size.
        """
        return ctypes.sizeof(self)

    @classmethod
    def new(cls):
        """Create an instance of class.

        Returns:
            An object.
        """
        mem = bytearray(ctypes.sizeof(cls))

        return cls.from_buffer(mem)

class Fanotify(object):
    """Wrapper class of fanotify"""

    def __init__(self):
        self.fd = -1

    def __del__(self):
        self.close()

    def init(self, flags, event_f_flags):
        self.fd = libc.fanotify_init(flags, event_f_flags)

        panic_on(self.fd < 0, os.strerror(ctypes.get_errno()))

    def mark(self, flags, mask, dirfd, path):
        rc = libc.fanotify_mark(self.fd, flags, mask, dirfd, path)

        panic_on(rc != 0, os.strerror(ctypes.get_errno()))

    def fileno(self):
        return self.fd

    def read(self):
        event = Event.new().init()
        bytes = libc.read(self.fd, event.reference(), event.size())

        panic_on(bytes <= 0, os.strerror(ctypes.get_errno()))

        return event

    def reply(self, event, response):
        panic_on(self.fd < 0, "Invalid file descriptor")
        panic_on(event.fd < 0, "Invalid file descriptor")

        response = Response.new().init(event.fd, response)
        bytes = libc.write(self.fd, response.reference(), response.size())

        panic_on(bytes <= 0, os.strerror(ctypes.get_errno()))

    def close(self):
        if self.fd >= 0:
            libc.close(self.fd)
            self.fd = -1

class Event(cstructure):
    """Interface of `struct fanotify_event_metadata`."""

    _fields_ = [
        ("event_len",    ctypes.c_uint32),
        ("vers",         ctypes.c_uint8),
        ("reserved",     ctypes.c_uint8),
        ("metadata_len", ctypes.c_uint16),
        ("mask",         ctypes.c_uint64),
        ("fd",           ctypes.c_int32),
        ("pid",          ctypes.c_int32),
    ]

    def __del__(self):
        self.close()

    def init(self):
        self.event_len = 0
        self.vers = 0
        self.reserved = 0
        self.metadata_len = 0
        self.mask = 0
        self.fd = -1
        self.pid = 0

        return self

    def close(self):
        if self.fd >= 0:
            libc.close(self.fd)
            self.fd = -1

class Response(cstructure):
    """Interface of `struct fanotify_response`."""

    _fields_ = [
        ("fd",       ctypes.c_int32),
        ("response", ctypes.c_uint32),
    ]

    def init(self, fd, response):
        self.fd = fd
        self.response = response

        return self

def describe(mask):
    masks = []

    if mask & OPEN_PERM:
        masks.append("OPEN_PERM")
    if mask & OPEN:
        masks.append("OPEN")
    if mask & ACCESS_PERM:
        masks.append("ACCESS_PERM")
    if mask & ACCESS:
        masks.append("ACCESS")
    if mask & MODIFY:
        masks.append("MODIFY")
    if mask & CLOSE_WRITE:
        masks.append("CLOSE_WRITE")
    if mask & CLOSE_NOWRITE:
        masks.append("CLOSE_NOWRITE")
    if mask & Q_OVERFLOW:
        masks.append("Q_OVERFLOW")
    if mask & ONDIR:
        masks.append("ONDIR")
    if mask & EVENT_ON_CHILD:
        masks.append("EVENT_ON_CHILD")

    return " | ".join(masks)

panic_on(not hasattr(libc, "fanotify_init"), "symbol `fanotify_init` not found")
panic_on(not hasattr(libc, "fanotify_mark"), "symbol `fanotify_mark` not found")
