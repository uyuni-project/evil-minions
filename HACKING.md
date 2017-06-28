# Development instructions

## Inspect dump files

In order to inspect dump files, you can use [msgpack-tools](https://github.com/ludocode/msgpack-tools):

```
msgpack2json -Cpi minion-dump.mp
```

## Update the package in openSUSE Build Service

```
osc service disabledrun                    # update sources
osc build SLE_12_SP2                       # local build dry run
osc vc -m "description of changes"         # update changelog
osc add evil-minions-$NEW_VERSION.tar.xz   # track new tarball
osc rm evil-minions-$OLD_VERSION.tar.xz    # remove old tarball
osc commit                                 # hey ho let's go!
```
