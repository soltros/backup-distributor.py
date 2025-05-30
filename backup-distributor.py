import os
import argparse
import shutil
from pathlib import Path

MANIFEST_FILENAME = ".backup_manifest.txt"

def get_all_files(source_dir):
    files = []
    for root, _, filenames in os.walk(source_dir):
        for fname in filenames:
            fpath = os.path.join(root, fname)
            try:
                size = os.path.getsize(fpath)
                files.append((fpath, size))
            except Exception:
                print(f"Skipping unreadable file: {fpath}")
    return files

def bytes_to_human(n):
    for unit in ['B','KiB','MiB','GiB','TiB']:
        if n < 1024.0:
            return f"{n:.2f} {unit}"
        n /= 1024.0
    return f"{n:.2f} PiB"

def parse_drive_specs(drive_specs):
    drives = []
    for spec in drive_specs:
        if ':' not in spec:
            raise ValueError(f"Invalid drive spec format: {spec}. Use LABEL:SIZE_MiB")
        label, size_str = spec.split(':', 1)
        size_bytes = int(size_str) * 1024 * 1024
        drives.append((label, size_bytes))
    return drives

def distribute_files(files, drives):
    allocation = {label: [] for label, _ in drives}
    used = {label: 0 for label, _ in drives}

    for path, size in sorted(files, key=lambda x: -x[1]):
        for label, max_size in drives:
            if used[label] + size <= max_size:
                allocation[label].append((path, size))
                used[label] += size
                break
        else:
            raise RuntimeError(f"Cannot fit file: {path} ({bytes_to_human(size)})")
    return allocation, used

def check_mountpoint(mountpoint):
    if not os.path.ismount(mountpoint):
        raise RuntimeError(f"{mountpoint} is not mounted! Please connect the drive and try again.")

def load_manifest(drive_path):
    manifest_path = Path(drive_path) / MANIFEST_FILENAME
    if not manifest_path.exists():
        return set()
    with open(manifest_path, "r") as f:
        return set(line.strip() for line in f)

def write_manifest(drive_path, files):
    manifest_path = Path(drive_path) / MANIFEST_FILENAME
    with open(manifest_path, "w") as f:
        for fpath, _ in files:
            f.write(f"{fpath}\n")

def copy_files(files, source_dir, dest_root, dry_run=False):
    for fpath, _ in files:
        rel = Path(fpath).relative_to(source_dir)
        dest = Path(dest_root) / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dry_run:
            print(f"[DRY-RUN] Would copy: {fpath} -> {dest}")
        else:
            print(f"Copying: {fpath} -> {dest}")
            shutil.copy2(fpath, dest)

def main():
    parser = argparse.ArgumentParser(description="Stage backup from one source folder to multiple drives (one at a time).")
    parser.add_argument("--source", required=True, help="Directory to back up")
    parser.add_argument("--drive", required=True, action='append', help="Drive spec: LABEL:SIZE_MiB")
    parser.add_argument("--output", default="/mnt/backup", help="Mount point for target drive (default: /mnt/backup)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate only; no files copied")
    args = parser.parse_args()

    source_dir = os.path.abspath(args.source)
    output_mount = os.path.abspath(args.output)

    print(f"🔍 Scanning {source_dir}...")
    files = get_all_files(source_dir)
    total_size = sum(size for _, size in files)
    print(f"Found {len(files)} files totaling {bytes_to_human(total_size)}")

    drives = parse_drive_specs(args.drive)
    allocation, used = distribute_files(files, drives)

    for label, _ in drives:
        print(f"\n🔋 Stage for drive: {label}")
        print(f"  Assigned {len(allocation[label])} files ({bytes_to_human(used[label])})")

        input(f"\n🔌 Connect drive '{label}' and press Enter when mounted at {output_mount}...")

        try:
            check_mountpoint(output_mount)
        except RuntimeError as e:
            print(f"❌ {e}")
            return

        manifest_files = load_manifest(output_mount)
        if manifest_files:
            print(f"✅ {label} already processed. Skipping.")
            continue

        copy_files(allocation[label], source_dir, output_mount, dry_run=args.dry_run)
        if not args.dry_run:
            write_manifest(output_mount, allocation[label])
            print(f"📝 Manifest written to {output_mount}/{MANIFEST_FILENAME}")

        print(f"\n✅ Done with {label}. You may now unmount the drive.")

    print("\n🎉 All stages complete.")

if __name__ == "__main__":
    main()
