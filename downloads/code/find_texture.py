#!/usr/bin/env python
# coding:utf-8
# find duplicate png in tp projects

import sys
import getopt
import os
import hashlib
import filecmp


TEXTURE_ROOT = 'tp_proj'
HASH_FUNC = hashlib.sha512
DEFAULT_LANG = 'en'


def get_pwd():
    return os.path.abspath(os.path.dirname(__file__))


def chunk_reader(fobj, chunk_size=1024):
    # Reference:
    # http://stackoverflow.com/questions/748675/finding-duplicate-files-and-removing-them
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk


def gen_hash_obj(file_name):
    hashobj = HASH_FUNC()
    for chunk in chunk_reader(open(file_name, 'rb')):
        hashobj.update(chunk)
    return hashobj


def update_dir_hashmap(path, hashmap_list):
    for root, dirs, files in os.walk(path):
        for file_name in files:
            full_path = os.path.abspath(os.path.join(root, file_name))
            hashobj = gen_hash_obj(full_path)
            file_id = hashobj.hexdigest()
            for hashmap in hashmap_list:
                duplicate_info = hashmap.get(file_id)

                if duplicate_info is None:
                    duplicate_info = set()

                duplicate_info.add(full_path)
                hashmap[file_id] = duplicate_info


def find_duplicates(input_dir, lang):
    pwd = get_pwd()
    search_path = pwd + TEXTURE_ROOT + lang
    print "Comparing %s and %s" % (input_dir, search_path)

    total_hashmap = {}
    input_dir_hashmap = {}
    update_dir_hashmap(search_path, [total_hashmap])
    update_dir_hashmap(input_dir, [total_hashmap, input_dir_hashmap])

    for k, v in input_dir_hashmap.items():
        duplicate_info = total_hashmap.get(k)
        if len(duplicate_info) > 1:
            print "========================================"
            print "The following %s files are duplicated:" % len(duplicate_info)
            for file_path in duplicate_info:
                print file_path


def find_file(input_file, lang):
    pwd = get_pwd()
    search_path = pwd + TEXTURE_ROOT + lang
    print "Searching %s in %s" % (input_file, search_path)

    isFound = None
    for root, dirs, files in os.walk(search_path):
        for file_name in files:
            full_path = os.path.join(root, file_name)
            if filecmp.cmp(input_file, full_path):
                print "The texture is already added as: %s." % full_path
                isFound = True
                if not isFound:
                    print "The texture has not been added: %s." % input_file


def usage():
    print 'Usage: ' + sys.argv[0] + ' -f <texture file> -d <dir> [-l <lang>]'


def main(argv):
    lang = DEFAULT_LANG
    input_dir = None
    input_file = None
    try:
        opts, args = getopt.getopt(argv, "hf:d:l:", ['help',
                                                     'file=',
                                                     'dir=',
                                                     'lang='])
        if not opts:
            print 'No options supplied'
            usage()
    except getopt.GetoptError as err:
        sys.stderr.write(str(err))
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-f', '--file'):
            input_file = arg
        elif opt in ('-d', '--dir'):
            input_dir = arg
        elif opt in ('-l', '--lang'):
            lang = arg
        elif opt in ('-h', '--help'):
            usage()
            sys.exit()

    if input_dir:
        find_duplicates(input_dir, lang)

    if input_file:
        find_file(input_file, lang)


if __name__ == "__main__":
    main(sys.argv[1:])
