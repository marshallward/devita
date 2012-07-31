#!/usr/bin/env python
# Playstation Vita System Object File dump
# Contact: Marshall Ward (marshall.ward@gmail.com)

import struct
import binascii

HEADER_BYTES = 20

class sfo(object):
    
    def __init__(self, filename=None):
        if fname:
            self.filename = fname
            self.load(filename)
    

    def load(self, filename):
        sfo_file = open(filename, 'rb')
        
        #---
        # Parse header
        header_raw = sfo_file.read(HEADER_BYTES)
        header = struct.unpack('<4s4BIII', header_raw)
        
        self.file_signature = header[0]
        self.file_version = '.'.join([str(h) for h in header[1:4]])
        
        # Variable and data references
        name_table_start = header[5]
        data_table_start = header[6]
        n_params = header[7]
        
        # Addressing
        def_table_bytes = 16 * n_params
        name_table_bytes = data_table_start - name_table_start
        def_table_padding = name_table_start - HEADER_BYTES - def_table_bytes
        
        # Ensure sufficient space for the parameter definition data
        assert def_table_padding >= 0
        
        #---
        # Parse definition table
        def_table = []
        for e in range(n_params):
            def_rec_raw = sfo_file.read(16)
            def_record = struct.unpack('<HHIII', def_rec_raw)
            def_table.append(def_record)
        
        # Read past and padded space between the definition and name tables
        # TODO: May be able to eliminate this
        sfo_file.read(def_table_padding)
        
        #---
        # Parse parameter names
        param_names = []
        for e in range(n_params):
            try:
                p_name_bytes = def_table[e+1][0] - def_table[e][0]
            except IndexError:
                p_name_bytes = name_table_bytes - def_table[e][0]
            p_name = sfo_file.read(p_name_bytes)
            param_names.append(p_name.rstrip('\x00'))
        
        #---
        # Parse parameter values
        param_values = []
        for e in range(n_params):
            # TODO: Maybe use def_table[4] (addressing) rather than byte size
            v_type  = def_table[e][1]
            v_bytes = def_table[e][2]
            v_total = def_table[e][3]
            
            value_raw = sfo_file.read(v_total)
            
            if v_type in (0x0204, 0x0004):
                value = value_raw
            elif v_type == 0x0404:
                value = int(binascii.hexlify(value_raw[::-1]))
            else:
                print 'unknown format'
            
            param_values.append(value)

        self.params = dict(zip(param_names, param_values))

        sfo_file.close()
    
    
    def dump(self):
        print 'SFO File Signature:', self.file_signature
        print 'SFO File Version:', self.file_version
        
        for p in self.params:
            print "{}: {}".format(p, self.params[p])


if __name__ == '__main__':
    
    # TODO: Read file from command line
    fname = 'param.sfo'
    test = sfo(fname)
    test.dump()
