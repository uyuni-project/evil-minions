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

mkdir -p /etc/systemd/system/salt-minion.service.d
cp override.conf /etc/systemd/system/salt-minion.service.d
```

### Usage

Starting salt-minion will automatically spawn any configured evil minions (10 by default). `systemd` is used in order to work correctly in case the minion service is restarted.

Every time the original minion receives and responds to a command, the command itself and the responses are "learned" by evil minions which will subsequently be able to respond to the same command. In practice, issuing the same command to all minions will work, eg.

`salt '*' test.ping`

evil minions will wait if presented with a command they have not learnt yet from the original minion.

Several parameters can be changed via commandline options in `/etc/systemd/system/salt-minion.service.d/override.conf`.

#### `--count` <number of evil minions>

The number of evil minions can can be changed via the `--count` commandline switch.

Simulating minions is not very resource intensive:
 - each evil-minon consumes ~2 MB of main memory, so thousands can be fit on a modern server
 - ~1000 evil-minions can be simulated at full speed (or near full speed) on one modern x86_64 core (circa 2018)
   - this means that a hypervisor vCPU, typically mapped to one HyperThread, will be able to support hundreds of evil minions

`evil-minions` combines [multiprocessing](https://docs.python.org/3.4/library/multiprocessing.html) and [Tornado](https://www.tornadoweb.org/en/stable/) to fully utilize available CPUs.

#### `--slowdown-factor` <number>

By default, evil minions will respond as fast as possible, which might not be appropriate depending on the objectives of your simulation. To reproduce delays observed by the original minion from which the dump was taken, use the `--slowdown-factor` switch:
 - `0.0`, the default value, makes evil minions respond as fast as possible
 - `1.0` makes `evil-minion` introduce delays to match the response times of the original minion
 - `2.0` makes `evil-minion` react twice as slow as the original minion
 - `0.5` makes `evil-minion` react twice as fast as the original minion

#### Other parameters

Please, use `evil-minions --help` to get the detailed list.

### Known limitations
 - only the ZeroMQ transport is supported
 - only `*` and exact minion id targeting are supported at the moment
 - some Salt features are not faithfully reproduced: `mine` events, `beacon` events, and `state.sls`'s `concurrent` option
