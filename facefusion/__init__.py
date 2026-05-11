import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
if backend_dir not in sys.path:
	sys.path.insert(0, backend_dir)

__path__ = [ os.path.join(backend_dir, 'facefusion') ]
