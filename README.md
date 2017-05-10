## evil-minions

![Evil Minions from the movie Despicable Me 2](https://vignette3.wikia.nocookie.net/despicableme/images/5/52/Screenshot_2016-02-10-01-09-16.jpg/revision/latest?cb=20161028002525)

`evil-minions` is a load generator for [Salt Open](https://saltstack.com/salt-open-source/). It is being developed at SUSE to aid [SUSE Manager](https://www.suse.com/products/suse-manager/) scalability testing.

### Status

Ongoing development, minimal functionality is there.

### Installation

 - install salt-minion 2015.8.12
 - clone this git repository

### Ideas and Usage

This project contains a script, `dumping-salt-minion`, that runs `salt-minion` while dumping all ZeroMQ traffic into a `/tmp/minion-dump.yml` file.

```
./dumping-salt-minion
# will create /tmp/minion-dump.yml
```

This "dump" can be fed to the `evil-minions` script, which will mimic the original minion by sending the same responses to equivalent requests coming from the master. It will by default simulate 10 copies of the original minion; the count can be changed via a commandline switch:

```
./evil-minions --count 5 <MASTER_FQDN>
```

Simulating minions is not very resource intensive, as one minion will typically consume:
 - ~10 open files (use `ulimit -n <10 * COUNT>` to increase the limit prior running `evil-minions`)
 - ~2 MB of main memory
 - ~0.1% of a modern x86_64 core (circa 2016)

By default, `evil-minions` will respond as fast as possible, which might not be appropriate depending on the objectives of your simulation. To reproduce delays observed by the original minion from which the dump was taken, use the `--slowdown-factor` switch:

```
./evil-minions --count 5 --slowdown-factor 1 <MASTER_FQDN>
```

`--slowdown-factor` can be any positive floating-point value, for example:
 - `0.0`, the default value, makes `evil-minions` respond as fast as possible
 - `1.0` makes `evil-minion` introduce delays to match times observed and recorded in `minion-dump.yml`
 - `2.0` makes `evil-minion` react twice as slow as the times observed and recorded in `minion-dump.yml`
 - `0.5` makes `evil-minion` react twice as fast as the times observed and recorded in `minion-dump.yml`

### Known limitations
 - only the ZeroMQ transport is supported
 - only `*` and exact minion id targeting are supported at the moment
 - delays between responses are not reproduced
 - some Salt features are not faithfully reproduced: `mine` events, `beacon` events, and `state.sls`'s `concurrent` option
