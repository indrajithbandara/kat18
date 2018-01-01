import logging
import sys

import kat18.client


logging.basicConfig(level='INFO')


if len(sys.argv) != 2:
    print(f'USAGE: {sys.argv[0]} config-path')
    exit(1)
else:
    kat18.client.KatBot(sys.argv[1]).run()
