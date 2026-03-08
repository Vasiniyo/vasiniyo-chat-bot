import argparse
import os
from pathlib import Path
import sys


def setup_instance():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-i", "--instance")
    args, _ = parser.parse_known_args()

    instances_dir = Path(__file__).resolve().parent.parent / "instances"

    # Allows to run bot both id docker and directly:
    # Direct run would require `instance` arg.
    if not args.instance:
        if Path("config.toml").exists():
            return

        available = (
            [d.name for d in instances_dir.iterdir() if d.is_dir()]
            if instances_dir.exists()
            else []
        )

        print("Usage: python src/main.py -i|--instance <name>")
        print(
            f"Available instances: {', '.join(sorted(available)) if available else '{}'}"
        )
        sys.exit(1)

    inst_dir = instances_dir / args.instance
    if not inst_dir.is_dir():
        print(f"Instance directory not found: {inst_dir}")
        sys.exit(1)

    env_file = inst_dir / ".env-instance"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    os.environ["CONFIG_PATH"] = str(inst_dir / "config.toml")

    data_dir = inst_dir / "data"
    data_dir.mkdir(exist_ok=True)
    os.environ["DATABASE_PATH"] = str(data_dir / "database.db")

    os.environ["INSTANCE_NAME"] = args.instance
