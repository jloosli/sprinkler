#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""
Sprinkler REST Server
Borrowed heavily from http://blog.miguelgrinberg.com/post/designing-a-restful-api-using-flask-restful
"""

import sys
import os
import traceback
import argparse
import time
import logging
from flask import Flask
from flask.ext.restful import Api, Resource, reqparse, fields, marshal
import sprinkler


# create file handler which logs even debug messages
log = logging.getLogger()
log.setLevel(logging.DEBUG)  # DEBUG | INFO | WARNING | ERROR | CRITICAL
formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(name)s - Ln. %(lineno)d\n%(message)s')
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
s = sprinkler.Scheduler()

baseUrl = '/sprinkler/api/v1.0/'

class UserAPI(Resource):
    def get(self, id):
        pass

    def put(self, id):
        pass

    def delete(self, id):
        pass

api.add_resource(UserAPI, baseUrl + 'users/<int:id>', endpoint = 'user')

program_fields = {
    'start': fields
}


class ProgramListAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, required=True,
            help='No program title provided', location='json')
        self.reqparse.add_argument('description', type=str, default="", location='json')
        super().__init__()

    def get(self):
        print([x for x in s.getPrograms()])
        return [x for x in s.getPrograms()]

    def post(self):
        pass


class ProgramAPI(Resource):
    def __init__(self):
        ''' Post is the only thing that receives reqparse arguments '''
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('start', type=str, location='json')
        self.reqparse.add_argument('zones', type=str, location ='json')
        super().__init__()

    def get(self, id):
        return {'program': 'bob'}

    def put(self, id):
        program = filter(lambda p: p['id'] == id, programs)
        if len(program) == 0:
            abort(404)
        program = program[0]
        args = self.reqparse.parse_args()
        program['start'] = args.get('start', program['start'])
        program['zones'] = args.get('zones', program['zones'])
        return { 'program': make_public_program(program) }

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
    app.run(debug="True")



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
