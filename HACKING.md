# Development instructions

## Update the package in openSUSE Build Service

```bash
osc rm evil-minions-*.tar.xz        # remove old tarball
osc service disabledrun             # update sources
osc build                           # local build dry run
osc vc -m "description of changes"  # update changelog
osc add evil-minions-*.tar.xz       # track new tarball
osc commit                          # hey ho let's go!
```
