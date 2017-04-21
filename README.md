## evil-minions

![Evil Minions from the movie Despicable Me 2](https://vignette3.wikia.nocookie.net/despicableme/images/5/52/Screenshot_2016-02-10-01-09-16.jpg/revision/latest?cb=20161028002525)

`evil-minions` is a load generator for [Salt Open](https://saltstack.com/salt-open-source/). It is being developed at SUSE to aid [SUSE Manager](https://www.suse.com/products/suse-manager/) scalability testing.

### Status

Ongoing development, functionality is less than minimal at this point (can get a key accepted and respond to `test.ping` on a single minion).

### Installation

 - install salt-minion 2015.8.12
 - clone this git repository

### Usage

```
vim evil-minions.py # hack opts
./evil-minions.py
```

### Hacking

The concept behind `evil-minions` is to simulate minions at the transport level (currently zeromq only). Base transport classes from Salt are used in order not to re-implement object serialization, encryption, authentication and network communication. Other than that, all else is faked.

You might want to get a trace of zeromq events from a real minion in order to hack on `evil-minions`, and you can do that with the `tracing-salt-minion` helper script - it will start `salt-minion` while monkey patching transport classes so that a `/tmp/minion-trace.txt` file. This currently does not work on Windows. Usage:

```
./tracing-salt-minion
```
