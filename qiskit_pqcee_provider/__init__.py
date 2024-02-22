from .provider import BlockchainProvider
from .provider import LocalPqceeProvider
from .provider import PqceeProvider
from .backend import BlockchainBackend
from .job import BlockcahinJob

__author__ = "Stefan-Dan Ciocirlan (sdcioc)"
__copyright__ = "Copyright 2023, Singapore Blockchain Innovation Programme"
__credits__ = ["Teik Guan Tan", "Sian (Jonathan) Liu"]
__license__ = "MIT"
__maintainer__ = "Stefan-Dan Ciocirlan"
__email__ = "stefan_dan@xn--ciocrlan-o2a.ro"
__status__ = "Production"

__all__ = [
    "quic",
    "BlockchainProvider",
    "BlockchainBackend",
    "BlockcahinJob",
    "LocalPqceeProvider",
    "PqceeProvider",

]

# read the verison from the file
import pathlib

# the current directory
ROOT_DIR = pathlib.Path(__file__).absolute().parent

# the version file
VERSION_FILE = (ROOT_DIR / "VERSION.txt").resolve()

# read the version
with open(VERSION_FILE, "r") as version_file:
    VERSION = version_file.read().strip()

__version__ = VERSION
# install solc if not already installed
import solcx

try:
    solcx.install.get_executable(version='0.8.21')
except solcx.exceptions.SolcNotInstalled:
    solcx.install_solc(version='0.8.21')
