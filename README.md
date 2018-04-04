## evil-minions

![Evil Minions from the movie Despicable Me 2](https://vignette3.wikia.nocookie.net/despicableme/images/5/52/Screenshot_2016-02-10-01-09-16.jpg/revision/latest?cb=20161028002525)

`evil-minions` is a load generator for [Salt Open](https://saltstack.com/salt-open-source/). It is being developed at SUSE to aid [SUSE Manager](https://www.suse.com/products/suse-manager/) scalability testing.

### Usage

`evil-minions` is composed of two tools:
 - a monkey-patching `salt-minion` script that "records" the behavior of a Salt minion to a dump file
 - an `evil-minions` script which is able to "play back" a dump file multiple times in parallel

The recommended way to use evil-minions is with [sumaform](https://github.com/moio/sumaform). If you are already using it, just follow the [sumaform-specific instructions](https://github.com/moio/sumaform/blob/master/README_ADVANCED.md#evil-minions-load-generator).

### Manual usage (recording)

 - Clone this git repository
 - Install Python dependencies:

```
~/evil-minions $ pip install -r requirements.txt
```
 - Patch the systemd unit file for `salt-minion`, eg. `/usr/lib/systemd/system/salt-minion.service`, changing the following line:
```
ExecStart=/root/evil-minions/dumping-salt-minion
```

then running `sudo systemctl daemon-reload`.

After starting `salt-minion` a dump of all ZeroMQ traffic will be created in `/tmp/minion-dump.mp`.

### Manual usage (playback)

 - Collect a dump file (see previous section)
 - Clone this git repository
 - Optionally, create and activate a new Python virtualenv:

```
~ $ cd evil-minions
~/evil-minions $ virtualenv myvirtualenv
~/evil-minions $ . myvirtualenv/bin/activate
```

 - Install Python dependencies:

```
(myvirtualenv) ~/evil-minions $ pip install -r requirements.txt
```
 
 - run the `evil-minions` script, pointing it to the dump file.


By default the `evil-minions` script will mimic the original minion by sending the same responses to equivalent requests coming from the master. It will by default simulate 10 copies of the original minion; the count can be changed via a commandline switch:

```
(myvirtualenv) ~/evil-minions $ ./evil-minions --count 5 <MASTER_FQDN>
```

Simulating minions is not very resource intensive, as one minion will typically consume:
 - ~10 open files (use `ulimit -n <10 * COUNT>` to increase the limit prior running `evil-minions`)
 - ~2 MB of main memory
 - ~0.1% of a modern x86_64 core (circa 2016)

By default, `evil-minions` will respond as fast as possible, which might not be appropriate depending on the objectives of your simulation. To reproduce delays observed by the original minion from which the dump was taken, use the `--slowdown-factor` switch:

```
(myvirtualenv) ~/evil-minions $ ./evil-minions --count 5 --slowdown-factor 1 <MASTER_FQDN>
```

`--slowdown-factor` can be any positive floating-point value, for example:
 - `0.0`, the default value, makes `evil-minions` respond as fast as possible
 - `1.0` makes `evil-minion` introduce delays to match times observed and recorded in `minion-dump.mp`
 - `2.0` makes `evil-minion` react twice as slow as the times observed and recorded in `minion-dump.mp`
 - `0.5` makes `evil-minion` react twice as fast as the times observed and recorded in `minion-dump.mp`


Extra tunning of `evil-minions` is allowed via command line parameters.
Please, use `evil-minions --help` to get the detailed list.

### Known limitations
 - only the ZeroMQ transport is supported
 - only `*` and exact minion id targeting are supported at the moment
 - some Salt features are not faithfully reproduced: `mine` events, `beacon` events, and `state.sls`'s `concurrent` option
