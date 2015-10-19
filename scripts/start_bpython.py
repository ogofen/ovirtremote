from ovirtremotesdk.ovirtremote import OvirtRemote
from ovirtsdk.xml import params
import sys

if len(sys.argv) > 1:
    ovirtremote = OvirtRemote(sys.argv[1])
