# Notes on setting up AppArmor:

## First, standard unix users, permissions:

```
$ sudo bash
$ addgroup sandbox
$ adduser --disabled-login sandbox --ingroup sandbox
```

Create a sandbox group.


We'll use a copy of python, because AppArmor restricts permissions per-file-path, and we want the normal python for running our server and such. (http://serverfault.com/questions/290828/creating-a-linux-sandbox-with-apparmor)

```
$ cp /usr/bin/python2.7 /usr/bin/python-sandbox
```

Let `makeitso` run python as the sandbox user:

```
$ visudo -f /etc/sudoers.d/01-sandbox
```

Content:
```
makeitso ALL=(sandbox) NOPASSWD: /usr/bin/python-sandbox
```


## Set up some process limits

In `/etc/security/limits.d/untrusted.conf`

```
sandbox       hard   core  0
sandbox       hard   data  100000
sandbox       hard   fsize 10000
sandbox       hard   memlock 10000
sandbox       hard   nofile 20
sandbox       hard   rss    10000
sandbox       hard   stack  100000
sandbox       hard   cpu    1
sandbox       hard   nproc  8
sandbox       hard   as     32000
sandbox       hard   maxlogins  1
sandbox       hard   priority  19
sandbox       hard   locks     4
sandbox       hard   sigpending  100
sandbox       hard   msgqueue  100000
sandbox       hard   nice     19
```

(these may not be the right params, but it's a start)


## Set up apparmor itself

apt-get install apparmor-utils


Making a profile for python-sandbox, in `/etc/apparmor.d/usr.bin.python-sandbox`

```
#include <tunables/global>

/usr/bin/python-sandbox {
  #include <abstractions/base>

  /usr/bin/python-sandbox mr,
  /usr/include/python2.7/** r,
  /usr/local/lib/python2.7/** r,
  /usr/lib/python2.7** rix,

  /tmp/** rix,
}}
```

Start enforcing it:
```
aa-enforce /usr/bin/python-sandbox
```

To see the apparmor config:

```
apparmor_status 
```


TODO:
- put code checking tests on a branch of 6.00x.  Deploy.
- Set it up.  Run mean tests.

