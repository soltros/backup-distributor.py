# backup-distributor.py
A simple tool that can calculate files you wish to backup and suggest a way to distribute them across drives. Comes with a ``--dry-run`` mode for simulation purposes.

**Step 1:**

```
lsblk -b -o NAME,SIZE,MOUNTPOINT
```
Or, for a list of mounted devices:

```
lsblk -o NAME,SIZE,MOUNTPOINT | grep "/mnt"
```

Then convert the byte size to MiB (or use ``lsblk -o NAME,SIZE -b --output-size`` if your distro supports it).

**Step 2:**
```
python backup_distributor.py --source "/MOUNT/POINT/" \
  --drive "MediaDrive1:2861588" \
  --drive "Archive2:1953513" \
  --dry-run
```
