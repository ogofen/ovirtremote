from ovirtsdk.api import API
from ovirtremotesdk.utils import collect_params
import sys

if len(sys.argv) > 1:
    setup = collect_params(sys.argv[1])
    print sys.argv[1]
    api = API(url=setup['url'], password=setup['password'],
              username='admin@internal', insecure=True)
