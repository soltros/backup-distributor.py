import os
import argparse
import shutil
from pathlib import Path

def get_all_files(source_dir):
    files = []
    for root, _, filenames in os.walk(source_dir):
        for fname in filenames:
            fpath = os.path.join(root, fname)
            try:
                size = os.path.getsize(fpath)
                files.append((fpath, size))
            except OSError:
                print(f"Skipping unreadable file: {fpath}")
    return files

def bytes_to_human(n):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024.0:
            return f"{n:.2f} {unit}"
        n /= 1024.0
    return f"{n:.2f} PB"

def parse_drive_specs(drive_specs):
    drives = []
    for spec in drive_specs:
        if ':' not in spec:
            raise ValueError(f"Invalid drive spec format: {spec}. Use LABEL:SIZE_GB format.")
        label, size_str = spec.split(':', 1)
        try:
            size_gb = int(size_str)
        except ValueError:
            raise ValueError(f"Invalid size for {label}: {size_str} must be an integer.")
        drives.append((label, size_gb * 1024**3))
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
            raise RuntimeError(f"Cannot fit file {path} ({bytes_to_human(size)}) into any drive")
    return allocation, used

def simulate_distribution(allocation, used, drives):
    for label, max_size in drives:
        print(f"\nDrive '{label}': Used {bytes_to_human(used[label])} / {bytes_to_human(max_size)}")
        for path, size in allocation[label]:
            print(f"  - {path} ({bytes_to_human(size)})")

def copy_files(allocation, base_output_path, dry_run=True):
    for label, files in allocation.items():
        out_base = Path(base_output_path) / label
        for fpath, _ in files:
            relative_path = Path(fpath).relative_to(base_output_path)
            dest = out_base / relative_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dry_run:
                print(f"[DRY-RUN] Would copy: {fpath} -> {dest}")
            else:
                shutil.copy2(fpath, dest)

def main():
    parser = argparse.ArgumentParser(description="Distribute files across multiple drives using label:size pairs.")
    parser.add_argument("--source", required=True, help="Source directory to back up")
    parser.add_argument("--drive", required=True, action='append', help="Drive spec format: LABEL:SIZE_GB (e.g., 'Media1:3000')")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without copying files")
    args = parser.parse_args()

    source_dir = os.path.abspath(args.source)
    print(f"Scanning {source_dir}...")

    files = get_all_files(source_dir)
    total_size = sum(size for _, size in files)
    print(f"Found {len(files)} files totaling {bytes_to_human(total_size)}")

    drives = parse_drive_specs(args.drive)

    print("\nDistributing files across:")
    for label, size in drives:
        print(f"  - {label}: {bytes_to_human(size)}")

    try:
        allocation, used = distribute_files(files, drives)
    except RuntimeError as e:
        print("Error:", e)
        return

    simulate_distribution(allocation, used, drives)

    if not args.dry_run:
        print("\nCopying files...")
        copy_files(allocation, source_dir, dry_run=False)
    else:
        print("\nDry run complete. No files copied.")

if __name__ == "__main__":
    main()
