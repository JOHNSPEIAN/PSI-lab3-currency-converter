"""Start the currency converter: ``python main.py [--help]``."""

import sys

from currency_converter.bootstrap import main

if __name__ == "__main__":
    sys.exit(main())
