## evil-minions

![Evil Minions from the movie Despicable Me 2](https://vignette3.wikia.nocookie.net/despicableme/images/5/52/Screenshot_2016-02-10-01-09-16.jpg/revision/latest?cb=20161028002525)

`evil-minions` is a load generator for [Salt Open](https://saltstack.com/salt-open-source/). It is being developed at SUSE to aid [SUSE Manager](https://www.suse.com/products/suse-manager/) scalability testing.

### Status

Ongoing development, functionality is less than minimal at this point (can get a key accepted and respond to `test.ping` on a single minion).

### Installation

 - install salt 2015.8.12
 - clone this git repository

### Usage

```
vim evil-minions.py # hack opts
./evil-minions.py
```
