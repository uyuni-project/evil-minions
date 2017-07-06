# Development instructions

## Inspect dump files

In order to inspect dump files, you can use [msgpack-tools](https://github.com/ludocode/msgpack-tools):

```bash
msgpack2json -cp <minion-dump.mp >minion-dump.json
```

You can also edit the JSON files and re-pack them later (manually or with a tool like [jq](https://stedolan.github.io/jq/)).

Re-packing is slightly more complicated because `json2msgpack` does not support continuous streams, can be accomplished with `bash` and `jq` by:

```bash
MESSAGE_COUNT=`jq -sc '. | length' <minion-dump.json`
for ((i=0; i<$MESSAGE_COUNT; i++)); do jq -sc .[$i] <minion-dump.json | json2msgpack >> minion-dump-repacked.mp; done
```

## Update the package in openSUSE Build Service

```bash
osc service disabledrun                    # update sources
osc build SLE_12_SP2                       # local build dry run
osc vc -m "description of changes"         # update changelog
osc add evil-minions-$NEW_VERSION.tar.xz   # track new tarball
osc rm evil-minions-$OLD_VERSION.tar.xz    # remove old tarball
osc commit                                 # hey ho let's go!
```
