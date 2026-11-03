"""python -m durweg: the same as the durweg command (durweg ui runs its commands this way)."""
import sys

from .cli import main

sys.exit(main())
