# Backup Stager: One-Drive-at-a-Time File Distributor

This script is designed to intelligently split a large folder (such as `/srv/media`) across multiple external drives — one drive at a time.

## Features
- Stage-based copy: connect **one drive at a time**
- Real usable space supported (MiB from `lsblk`)
- Logs a `.backup_manifest.txt` to mark drives as completed
- Resumable: skips already completed drives
- Dry run supported

##  Usage

```bash
python3 backup_stager.py \
  --source "/srv/media" \
  --drive "DriveA:2861588" \
  --drive "DriveB:1953513" \
  --output "/mnt/backup"
```

## 📦 How To Get MiB Sizes

Use:

```bash
lsblk -b -o NAME,SIZE,MOUNTPOINT
```

Then divide the `SIZE` in bytes by `1024^2` to get MiB.

##  Warning

Ensure your mountpoint (`/mnt/backup` by default) is mounted before continuing. The script will stop if it's not.

## Output

Each connected drive will receive a `.backup_manifest.txt` log with the files it was assigned.

##  Resetting

If you need to re-do a drive, just delete the `.backup_manifest.txt` file from its root.

---

Created for safe and repeatable staged backups from a server.

