#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012 Gert van Dijk (gertvdijk@gmail.com)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

try:
    import mechanize
    import mimetypes
    import sys
    from optparse import OptionParser
except ImportError:
    print("Some dependencies were not fulfilled on the system. Please check the requirements.", file=sys.stderr)
    raise

def errorout(s):
    print("error: " + s, file=sys.stderr)

def normalout(s):
    print(s)

def debugout(s):
    print("debug: " + s)
    
def run_optionparser():
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename", default=None,
                    help="specify the input FILE to upload", metavar="FILE")
    #parser.add_option("-c", "--config", dest="configfile",
    #                help="specify the configuration FILE to use (optional).\nOptions passed override configuration file parameters.", metavar="FILE")
    parser.add_option("-d", "--description", dest="description", default=None,
                    help="some DESCRIPTION of the file", metavar="DESCRIPTION")
    parser.add_option("-l", "--url", dest="url", default=None,
                    help="specify the URL of the Redmine installation", metavar="URL")
    parser.add_option("-p", "--project", dest="project", default=None,
                    help="Redmine project IDENTIFIER", metavar="IDENTIFIER")
    parser.add_option("-u", "--user", dest="user", default=None,
                    help="the USERNAME to connect to the Redmine installation", metavar="USERNAME")
    parser.add_option("-w", "--password", dest="password", default=None,
                    help="the PASSWORD to connect to the Redmine installation", metavar="PASSWORD")
    parser.add_option("-q", "--quiet",
                    action="store_true", dest="quiet", default=False,
                    help="Don't output error messages.")
    parser.add_option("-v", "--verbose",
                    action="store_true", dest="verbose", default=False,
                    help="Print status messages to stdout.")
    
    return parser.parse_args()

class RedmineFileUploader(object):
    
    def __init__(self, options):
        if options.verbose:
            self.debugout = debugout
        else:
            self.debugout = lambda s: None
        
        if not options.quiet:
            self.errorout = errorout
            self.normalout = normalout
        else:
            self.errorout = lambda s: None
            self.normalout = lambda s: None
        
        self.url = options.url
        self.project_id = options.project
        self.username = options.user
        self.password = options.password
        self.filename = options.filename
        self.description = options.description
        self.content_type = None

    def run(self):
        self.browser = self.init_browser()
        self.the_file = self.open_file()
        self.login()
        self.open_file_page()
        self.populate_form()
        self.submit_file()
        
    def init_browser(self):
        br = mechanize.Browser()
        br.set_handle_robots(False)
        return br
        
    def login(self):
        self.debugout('Fetching ' + self.url + 'login page...')
        
        try:
            page = self.browser.open(self.url + 'login')
        except:
            self.errorout("Fatal: Could not open login page.")
            raise
        else:
            self.debugout("Login page opened")

        self.debugout('Logging in...')
        try:
            self.browser.select_form(predicate=lambda f: 'action' in f.attrs and f.attrs['action'].endswith('/login'))
            self.browser["username"] = self.username
            self.browser["password"] = self.password
            try:
                self.browser["autologin"] = 0
            except:
                pass
        except:
            self.errorout("Could not enter details in login form. Is your Redmine installation compatible?")
            raise
        
        try:
            page = self.browser.submit()
        except:
            self.errorout("Could not submit login form.")
            raise

    def open_file_page(self):
        self.debugout('Opening New Files page...')
        try:
            page = self.browser.open(str(self.url + 'projects/' + self.project_id + '/files/new'))
        except:
            self.errorout("Could not open 'Files' page for the project. Is 'Files' enabled for your project?")
            raise

    def populate_form(self):
        self.debugout('Registering the file')
        self.browser.select_form(predicate=lambda f: 'action' in f.attrs and f.attrs['action'].lower().endswith('/projects/' + self.project_id.lower() + '/files'))
        self.browser.add_file(self.the_file, self.content_type, self.description)
        #br["version_id"]= ["44"]
    
    def open_file(self):
        ''' Open and detect mimetype of the file. Returns file object. '''
        
        mimetypes.init()
        try:
            the_file = open(self.filename, "rb")
            self.debugout("file " + self.filename + " opened")
            (self.content_type, content_encoding) = mimetypes.guess_type(self.filename)
            self.debugout("Detected Content-type: " + self.content_type)
        except IOError:
            self.errorout("File specified could not be opened.")
            raise
        else:
            return the_file

    def submit_file(self):
        try:
            page = self.browser.submit()
        except:
            self.errorout("Form with file could not be submitted.")
            raise
        else:
            self.normalout('File sumitted!')

if __name__=="__main__":
    (options, args) = run_optionparser()
    if options.password is not None:
        normalout("Warning! Note that supplying password on the command line is discouraged as it can be seen in the processlist by every user on the system.")
    uploader = RedmineFileUploader(options)
    uploader.run()
