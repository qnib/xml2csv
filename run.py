#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""

Usage:
    run.py [options]

Options:
    --xml <path>            XML file to parse
Generic Options:
    --loglevel, -L=<str>    Loglevel [default: INFO]
                            (ERROR, CRITICAL, WARN, INFO, DEBUG)
    --log2stdout, -l        Log to stdout, otherwise to logfile. [default: False]
    --logfile, -f=<path>    Logfile to log to (default: <scriptname>.log)
    --cfg, -c=<path>        Configuration file.
    -h --help               Show this screen.
    --version               Show version.

"""

# load librarys
import logging
import os
import re
import time
import codecs
import ast
import sys
from ConfigParser import RawConfigParser, NoOptionError
from qnib_xml2csv import *

try:
    from docopt import docopt
except ImportError:
    HAVE_DOCOPT = False
else:
    HAVE_DOCOPT = True

__author__ = 'Christian Kniep <christian()qnib.org>'
__copyright__ = 'Copyright 2015 QNIB Solutions'
__license__ = """GPL v2 License (http://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)"""


class QnibConfig(RawConfigParser):
    """ Class to abstract config and options
    """
    specials = {
        'TRUE': True,
        'FALSE': False,
        'NONE': None,
    }

    def __init__(self, opt):
        """ init """
        RawConfigParser.__init__(self)
        if opt is None:
            self._opt = {
                "--log2stdout": False,
                "--logfile": None,
                "--loglevel": "ERROR",
            }
        else:
            self._opt = opt
            self.logformat = '%(asctime)-15s %(levelname)-5s [%(module)s] %(message)s'
            self.loglevel = opt['--loglevel']
            self.log2stdout = opt['--log2stdout']
            if self.loglevel is None and opt.get('--cfg') is None:
                print "please specify loglevel (-L)"
                sys.exit(0)
            self.eval_cfg()

        self.eval_opt()
        self.set_logging()
        logging.info("SetUp of QnibConfig is done...")

    def do_get(self, section, key, default=None):
        """ Also lent from: https://github.com/jpmens/mqttwarn
            """
        try:
            val = self.get(section, key)
            if val.upper() in self.specials:
                return self.specials[val.upper()]
            return ast.literal_eval(val)
        except NoOptionError:
            return default
        except ValueError:  # e.g. %(xxx)s in string
            return val
        except:
            raise
            return val

    def config(self, section):
        ''' Convert a whole section's options (except the options specified
                explicitly below) into a dict, turning

                    [config:mqtt]
                    host = 'localhost'
                    username = None
                    list = [1, 'aaa', 'bbb', 4]

                into

                    {u'username': None, u'host': 'localhost', u'list': [1, 'aaa', 'bbb', 4]}

                Cannot use config.items() because I want each value to be
                retrieved with g() as above
            SOURCE: https://github.com/jpmens/mqttwarn
            '''

        d = None
        if self.has_section(section):
            d = dict((key, self.do_get(section, key))
                     for (key) in self.options(section) if key not in ['targets'])
        return d

    def eval_cfg(self):
        """ eval configuration which overrules the defaults
            """
        cfg_file = self._opt.get('--cfg')
        if cfg_file is not None:
            fd = codecs.open(cfg_file, 'r', encoding='utf-8')
            self.readfp(fd)
            fd.close()
            self.__dict__.update(self.config('defaults'))

    def eval_opt(self):
        """ Updates cfg according to options """

        def handle_logfile(val):
            """ transforms logfile argument
                """
            if val is None:
                logf = os.path.splitext(os.path.basename(__file__))[0]
                self.logfile = "%s.log" % logf.lower()
            else:
                self.logfile = val

        self._mapping = {
            '--logfile': lambda val: handle_logfile(val),
        }
        for key, val in self._opt.items():
            if key in self._mapping:
                if isinstance(self._mapping[key], str):
                    self.__dict__[self._mapping[key]] = val
                else:
                    self._mapping[key](val)
                break
            else:
                if val is None:
                    continue
                mat = re.match("\-\-(.*)", key)
                if mat:
                    self.__dict__[mat.group(1)] = val
                else:
                    logging.info("Could not find opt<>cfg mapping for '%s'" % key)

    def set_logging(self):
        """ sets the logging """
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.DEBUG)
        if self.log2stdout:
            hdl = logging.StreamHandler()
            hdl.setLevel(self.loglevel)
            formatter = logging.Formatter(self.logformat)
            hdl.setFormatter(formatter)
            self._logger.addHandler(hdl)
        else:
            hdl = logging.FileHandler(self.logfile)
            hdl.setLevel(self.loglevel)
            formatter = logging.Formatter(self.logformat)
            hdl.setFormatter(formatter)
            self._logger.addHandler(hdl)

    def __str__(self):
        """ print human readble """
        ret = []
        for key, val in self.__dict__.items():
            if not re.match("_.*", key):
                ret.append("%-15s: %s" % (key, val))
        return "\n".join(ret)

    def __getitem__(self, item):
        """ return item from opt or __dict__
        :param item: key to lookup
        :return: value of key
        """
        if item in self.__dict__.keys():
            return self.__dict__[item]
        else:
            return self._opt[item]


class Xml2Csv(object):
    """ Class to hold the meat
    """

    def __init__(self, cfg):
        """ Init of instance
        """
        self._cfg = cfg
        self._xml = XmlObj(cfg)

    def loop(self):
        """  loop over run
        """
        while True:
            self.run()
            time.sleep(int(self._cfg['--delay']))

    def run(self):
        """ do the work
        """
        print self._cfg
        self._xml.parse()
        print self._xml


def main():
    """ main function """
    options = None
    if HAVE_DOCOPT:
        options = docopt(__doc__, version='Test Script 0.1')
    qcfg = QnibConfig(options)
    xml = Xml2Csv(qcfg)
    xml.run()


if __name__ == "__main__":
    main()
