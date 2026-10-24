"""Run gcw as ``python -m gcw``; used by the background cache refresh."""

import sys

from gcw.cli.main import main

sys.exit(main())
