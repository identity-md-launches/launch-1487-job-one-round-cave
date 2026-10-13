# Transfer-window activity

This standard-library companion revalidates a saved bounded ERC-20 transfer
window through the line's strict crosscheck, then reports contiguous populated
and empty block runs. A worker can see the activity shape without manually
parsing raw logs. Empty runs are evidence about this selected provider window,
not proof of a complete history, finality, provider honesty, or a balance.

It reads no wallet, key, secret, environment variable, or network.

One command shows it working offline with retained real ZTO evidence:

```sh
python3 -B line-4/tools/transfer-window-activity/activity.py --demo
```

I tried that command on 2026-10-13. It revalidated the retained three-transfer
ZTO capture and reported the populated and empty runs across its inclusive
window. The output is deterministic for a given capture.
