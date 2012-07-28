#!/usr/bin/env python
# Playstation Vita System Object File dump
# Contact: Marshall Ward (marshall.ward@gmail.com)

import struct

HEADER_BYTES = 20

class sfo(object):
    
    def __init__(self, filename=None):
        if fname:
            self.filename = fname
            self.load(filename)
    

    def load(self, filename):
        
        sfo_file = open(filename, 'rb')
        
        header_raw = sfo_file.read(HEADER_BYTES)
        header = struct.unpack('<4s4B', header_raw)

        self.file_signature = header[0]
        self.file_version = '.'.join([str(h) for h in header[1:4]])
        
        # Variable and data references
        name_table_start = 0
        data_table_start = 0
        n_entries = 0
        
        sfo_file.close()
    
    def dump(self):
        
        print 'File Signature:', self.file_signature
        print 'File Version:', self.file_version


if __name__ == '__main__':
    
    # TODO: Read file from command line
    fname = 'param.sfo'
    test = sfo(fname)
    test.dump()
