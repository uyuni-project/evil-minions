# Development instructions

## Update the package in openSUSE Build Service

```bash
osc service disabledrun                    # update sources
osc build SLE_12_SP2                       # local build dry run
osc vc -m "description of changes"         # update changelog
osc add evil-minions-$NEW_VERSION.tar.xz   # track new tarball
osc rm evil-minions-$OLD_VERSION.tar.xz    # remove old tarball
osc commit                                 # hey ho let's go!
```
