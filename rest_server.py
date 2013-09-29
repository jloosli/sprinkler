#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""
Sprinkler REST Server
"""

import sys
import os
import traceback
import argparse
import time
import logging
from flask import Flask
from flask.ext.restful import Api, Resource, reqparse


# create file handler which logs even debug messages
log = logging.getLogger()
log.setLevel(logging.DEBUG)  # DEBUG | INFO | WARNING | ERROR | CRITICAL
formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(name)s - Line: %(lineno)d\n%(message)s')
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
log.addHandler(sh)
fh = logging.FileHandler('sprinkler.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)

app = Flask(__name__)
api = Api(app)

baseUrl = '/sprinkler/api/v1.0/'

class UserAPI(Resource):
    def get(self, id):
        pass

    def put(self, id):
        pass

    def delete(self, id):
        pass

api.add_resource(UserAPI, baseUrl + 'users/<int:id>', endpoint = 'user')


class ProgramListAPI(Resource):
    def get(self):
        pass

    def post(self):
        pass


class ProgramAPI(Resource):
    def get(self, id):
        pass

    def put(self, id):
        pass

    def delete(self, id):
        pass

api.add_resource(ProgramListAPI, baseUrl + 'programs', endpoint = 'tasks')
api.add_resource(ProgramAPI, baseUrl + 'programs/<int:id>', endpoint = 'task')


class SystemAPI(Resource):
	def get(self, id):
		pass

api.add_resource(SystemAPI, baseUrl + 'system', endpoint='system')


def main():

    global args
    # TODO: Do something more interesting here...
    print('Hello world!')

if __name__ == '__main__':
    try:
        start_time = time.time()
        # Parser: See http://docs.python.org/dev/library/argparse.html
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('-v', '--verbose', action='store_true', default=False, help='verbose output')
        parser.add_argument('-ver', '--version', action='version', version='0.0.1')
        args = parser.parse_args()
        if args.verbose:
            fh.setLevel(logging.DEBUG)
            log.setLevel(logging.DEBUG)
        log.info("App Started")
        main()
        log.info("App Ended")
        log.info("Total running time in seconds: %0.2f" % (time.time() - start_time))
        sys.exit(0)
    except KeyboardInterrupt as e:  # Ctrl-C
        raise e
    except SystemExit as e:  # sys.exit()
        raise e
    except Exception as e:
        print('ERROR, UNEXPECTED EXCEPTION')
        print(str(e))
        traceback.print_exc()
        os._exit(1)
