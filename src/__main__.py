from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))


from setup_envs import setup_instance

setup_instance()

from main import run  # noqa: E402

run()
