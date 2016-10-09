#!/usr/bin/env python
#
# Script to remove duplicate files from a directory tree. Useful for
# photo backups on a NAS.
#
# TODO: add file extension options

from __future__ import print_function

import os, sys, getopt
import hashlib

CHUNK_SIZE = 65536
STATUS_UPDATE = 1000
VERBOSE = False
DO_DELETE = False

def get_hash(filename, first_chunk_only=False, hash=hashlib.sha1):
    hashobj = hash()
    fh = open(filename, 'rb')

    if first_chunk_only:
        hashobj.update(fh.read(CHUNK_SIZE))
    else:
        chunk = fh.read(CHUNK_SIZE)
        while len(chunk) > 0:
            hashobj.update(chunk)
            chunk = fh.read(CHUNK_SIZE)
    hashed = hashobj.digest()
    fh.close()
    return hashed

def check_for_duplicates(paths, hash=hashlib.sha1):
    hashes_by_size = {}

    # find all files
    print("searching over all files...")
    file_count = 0
    for path in paths:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                try:
                    file_size = os.path.getsize(full_path)
                except (OSError,):
                    pass

                file_count += 1
                if (STATUS_UPDATE > 0) and (file_count % STATUS_UPDATE == 0):
                    print("...{} files found".format(file_count))
                
                if file_size not in hashes_by_size:
                    hashes_by_size[file_size] = []
                hashes_by_size[file_size].append(full_path)

    # iterate through files of the same size getting their hash on the first chunk
    print("searching over {} sets by size...".format(len(hashes_by_size)))
    count = 0
    next_update = STATUS_UPDATE
    if next_update <= 0:
        next_update = file_count
    dup_count = 0
    for __, files in hashes_by_size.items():
        if len(files) < 2:
            count += 1
            continue 

        hashes_on_chunk = {}
        for filename in files:
            count += 1
            if count >= next_update:
                print("...{} of {} files processed ({} duplicates found)".format(count, file_count, dup_count))
                next_update = count + STATUS_UPDATE - (count % STATUS_UPDATE)

            small_hash = get_hash(filename, first_chunk_only=True)
            if small_hash not in hashes_on_chunk:
                hashes_on_chunk[small_hash] = []
            hashes_on_chunk[small_hash].append(filename)

        # iterate through all files with same (size and) hash on first chunk
        for __, files2 in hashes_on_chunk.items():
            if len(files2) < 2:
                continue 

            hashes_full = {}
            for filename in files2:
                full_hash = get_hash(filename, first_chunk_only=False)

                duplicate = hashes_full.get(full_hash)
                if duplicate:
                    dup_count += 1
                    if VERBOSE:
                        print("...duplicate found: {} and {}".format(filename, duplicate))
                    if DO_DELETE:
                        try:
                            os.remove(filename)
                        except (OSError,):
                            print("WARNING: could not delete {}".format(filename))                            
                else:
                    # record first file with full_hash (the rest are duplicates)
                    hashes_full[full_hash] = filename
        
    print("{} duplicates found".format(dup_count))


# --- main --------------------------------------------------------------

def usage(result=1):
    """Print usage statement."""
    print("USAGE: python " + sys.argv[0] + " [<OPTIONS>] (<DIRECTORY>)+")
    print("OPTIONS:")
    print("  --chunk|-c <n>   :: change chunk size (default: {})".format(CHUNK_SIZE))
    print("  --update|-u <n>  :: change update rate (default: {})".format(STATUS_UPDATE))
    print("  --verbose|-v     :: turn on verbose output")
    print("  --delete         :: delete duplicates")
    sys.exit(result)


def main():
    global CHUNK_SIZE, STATUS_UPDATE, VERBOSE, DO_DELETE

    # parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:u:v", ["chunk=", "update=", "verbose", "delete"])
    except getopt.GetoptError:
        usage()

    if len(args) == 0:
        usage()

    for opt, arg in opts:
        if opt in ("-c", "--chunk"):
            CHUNK_SIZE = max(1024, int(arg))
        elif opt in ("-u", "--update"):
            STATUS_UPDATE = int(arg)
        elif opt in ("-v", "--verbose"):
            VERBOSE = True
        elif opt in ("--delete"):
            DO_DELETE = True

    check_for_duplicates(args)


if __name__ == "__main__":
    main()

