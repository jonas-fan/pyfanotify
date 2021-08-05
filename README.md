# pyfanotify

Linux fanotify in python.

## Usage

**DO NOT** mointor the root `/`, otherwise operating system may hang.

```bash
$ sudo python3 main.py /run
path: '/run' (mountpoint: '/run')
[2021-08-05 21:25:58.596776] cat(1148116) | (OPEN_PERM) | /run/utmp
[2021-08-05 21:25:58.597675] ?(1148116) | (CLOSE_NOWRITE) | /run/utmp
[2021-08-05 21:25:59.828243] gsd-housekeepin(1963) | (OPEN_PERM) | /run/mount/utab
[2021-08-05 21:25:59.828578] gsd-housekeepin(1963) | (CLOSE_NOWRITE) | /run/mount/utab
[2021-08-05 21:25:59.828916] gsd-housekeepin(1963) | (OPEN_PERM) | /run/mount/utab
[2021-08-05 21:25:59.829121] gsd-housekeepin(1963) | (CLOSE_NOWRITE) | /run/mount/utab
```
