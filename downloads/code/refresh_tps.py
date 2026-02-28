#!/usr/bin/env python
# coding:utf-8
# Refresh TexturePacker *.tps

import sys
import os
import xml.sax
import cStringIO
# import string
import re
import shutil

CJK_REGEX = ur'[\u4e00-\u9fff]+'
# Configure your resource path here
# e.g. 'resources/${lang}/images', you should put 'resources/{1}/images'
DEFAULT_RES_PATH_FORMAT = 'XXX/{1}'
TP_PROJ_ROOT = 'tp_proj'


class TPSHandler(xml.sax.ContentHandler):
    def __init__(self, output, lang):
        self.output = output
        self.lang = lang
        self.tag = None
        self.key = None

    def startElement(self, tag, attributes):
        self.output.startElement(tag, attributes)
        self.tag = tag
        # print self.tag, self.key

    def endElement(self, tag):
        self.output.endElement(tag)

    # A simple way to check CJK characters
    # http://stackoverflow.com/questions/2718196/find-all-chinese-text-in-a-string-using-python-and-regex
    def containsCJK(self, string):
        return re.search(CJK_REGEX, string)

    def CJKAlert(self, key, content):
        print u"%s 含有中文字符: %s" % (key, content)

    def defaultResPath(self):
        return DEFAULT_RES_PATH_FORMAT.format(self.lang)

    def resetPath(self, content):
        return "%s/%s" % (
            self.defaultResPath(),
            os.path.basename(content),
        )

    def characters(self, content):
        if not content.isspace():
            if self.tag == 'key':
                self.key = content
            else:
                if self.key is not None:
                    if self.key == 'dataFormat':
                        content = 'cocos2d'
                    elif self.key == 'sizeConstraints':
                        content = 'AnySize'
                    elif self.key == 'textureFileName':
                        if self.containsCJK(content):
                            self.CJKAlert(self.key, content)
                            content = self.resetPath(content)
                    elif self.key == 'dataFileName':
                        if self.containsCJK(content):
                            self.CJKAlert(self.key, content)
                            content = self.resetPath(content)
                    elif self.key == 'javaFileName':
                        if self.containsCJK(content):
                            self.CJKAlert(self.key, content)
                            content = self.resetPath(content)

        self.output.characters(content)


def get_new_content(tps_file, lang):
    parser = xml.sax.make_parser()

    xml_content_buf = cStringIO.StringIO()
    xml_generator = xml.sax.saxutils.XMLGenerator(xml_content_buf, 'UTF-8')

    xml_generator.startDocument()

    parser.setContentHandler(TPSHandler(xml_generator, lang))
    parser.parse(open(tps_file, 'r'))

    xml_generator.endDocument()

    # print xml_content_buf.getvalue()
    return xml_content_buf


def write_tps_file(tps_file, buf):
    with open(tps_file, 'w') as fd:
        buf.seek(0)
        shutil.copyfileobj(buf, fd)


# From Python Cookbook
def splitall(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def get_lang(tps_file):
    full_path = os.path.abspath(tps_file)
    # Find last occurrence of TP_PROJ_ROOT in the full path
    path_regex = TP_PROJ_ROOT + '(.*)'
    postfix = re.findall(path_regex, full_path)[-1]
    # NOTE: the first element of postfix is '/' or '\'
    return splitall(postfix)[1]


def refresh_tps_file(tps_file):
    if not os.path.exists(tps_file):
        err_msg = "%s is not existed!" % tps_file
        sys.stderr.write(err_msg)
        sys.exit(1)

    lang = get_lang(tps_file)
    new_content = get_new_content(tps_file, lang)
    write_tps_file(tps_file, new_content)


def main(argv):
    tps_file = argv[0]
    if os.path.exists(tps_file):
        refresh_tps_file(tps_file)
    else:
        err_msg = "%s is not existed!" % tps_file
        sys.stderr.write(err_msg)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
