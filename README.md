## evil-minions

![Evil Minions from the movie Despicable Me 2](https://vignette3.wikia.nocookie.net/despicableme/images/5/52/Screenshot_2016-02-10-01-09-16.jpg/revision/latest?cb=20161028002525)

`evil-minions` is a load generator for [Salt Open](https://saltstack.com/salt-open-source/). It is used at SUSE for Salt, [Uyuni](https://www.uyuni-project.org/) and [SUSE Manager](https://www.suse.com/products/suse-manager/) scalability testing.

### Intro

`evil-minions` is a program that monkey-patches `salt-minion` in order to spawn a number of additional simulated "evil" minions alongside the original one.

Evil minions will mimic the original by responding to commands from the Salt master by copying and minimally adapting responses from the original one. Responses are expected to be identical apart from a few details like the minion ID (it needs to be different in order for the Master to treat them as separate).

Evil minions are lightweight - hundreds can run on a modern x86 core.

### Installation

[sumaform](https://github.com/moio/sumaform) users: follow [sumaform-specific instructions](https://github.com/moio/sumaform/blob/master/README_ADVANCED.md#evil-minions-load-generator)

SUSE distros: install via RPM package
```
# replace openSUSE_Leap_15.0 below with a different distribution if needed
zypper addrepo https://download.opensuse.org/repositories/systemsmanagement:/sumaform:/tools/openSUSE_Leap_15.0/systemsmanagement:sumaform:tools.repo
zypper install evil-minions
```

Other distros: install via pip
```
git checkout https://github.com/moio/evil-minions.git
cd evil-minions
pip install -r requirements.txt
```

### Usage

Copy the override.conf file from this repository to /etc/systemd/system/salt-minion.service.d and restart the salt-minion service:
```
mkdir -p /etc/systemd/system/salt-minion.service.d
cp evil-minions/override.conf /etc/systemd/system/salt-minion.service.d
systemctl daemon-reload
systemctl restart salt-minion
```

This is done automatically if you use sumaform.


By default the `evil-minions` script will mimic the original minion by sending the same responses to equivalent requests coming from the master. It will by default simulate 10 copies of the original minion; the count can be changed via the `--count` commandline switch in `override.conf`.

Simulating minions is not very resource intensive, as one minion will typically consume:
 - ~10 open files (use `ulimit -n <10 * COUNT>` to increase the limit prior running `evil-minions`)
 - ~2 MB of main memory
 - ~0.1% of a modern x86_64 core (circa 2016)

`evil-minions` combines [multiprocessing](https://docs.python.org/3.4/library/multiprocessing.html) and [Tornado](https://www.tornadoweb.org/en/stable/) to fully utilize available CPUs.

By default, `evil-minions` will respond as fast as possible, which might not be appropriate depending on the objectives of your simulation. To reproduce delays observed by the original minion from which the dump was taken, use the `--slowdown-factor` switch:
 - `0.0`, the default value, makes `evil-minions` respond as fast as possible
 - `1.0` makes `evil-minion` introduce delays to match times observed and recorded in `minion-dump.mp`
 - `2.0` makes `evil-minion` react twice as slow as the times observed and recorded in `minion-dump.mp`
 - `0.5` makes `evil-minion` react twice as fast as the times observed and recorded in `minion-dump.mp`

Extra tuning of `evil-minions` is allowed via command line parameters.
Please, use `evil-minions --help` to get the detailed list.

### Known limitations
 - only the ZeroMQ transport is supported
 - only `*` and exact minion id targeting are supported at the moment
 - some Salt features are not faithfully reproduced: `mine` events, `beacon` events, and `state.sls`'s `concurrent` option
