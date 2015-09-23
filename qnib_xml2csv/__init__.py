#! /usr/bin/env python
# -*- coding: utf-8 -*-


import yaml
#from xml.dom import minidom
import xml.etree.ElementTree as ET

class XmlObj(object):
    def __init__(self, cfg):
        self._cfg = cfg
        self._res = {
            'meta': {},
            'acct': [],
        }

    def parse(self):
        """ parses the file
        """
        tree = ET.parse(self._cfg['--xml'])
        root = tree.getroot()
        for parent in root:
            for child in parent:
                if child.tag == 'FAKTURA':
                    for item in child:
                        if item.tag == 'ABRECHNUNG':
                            acct = {}
                            for abr in item:
                                acct[abr.tag] = abr.text
                            self._res['acct'].append(acct)
                            del acct
                        else:
                            self._res['meta'][item.tag] = item.text
                else:
                    print "> ", child.tag

    def __str__(self):
        txt = []
        for key,val in self._res['meta'].items():
            if val is None:
                txt.append("# %-20s: <NULL>" % (key))
            else:
                txt.append("# %-20s: %s" % (key, val.encode('utf-8')))
        for acct in self._res['acct']:
            sub = []
            for key, val in acct.items():
                sub.append("%s:%s" %  (key, val.encode('utf-8')))
            if len(sub)>0:
                txt.append(",".join(sub))
        return "\n".join(txt)

