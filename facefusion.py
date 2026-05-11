#!/usr/bin/env python3

import os
import sys

os.environ['OMP_NUM_THREADS'] = '1'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from facefusion.utils import conda
from facefusion import core

if __name__ == '__main__':
	conda.setup()
	core.cli()
