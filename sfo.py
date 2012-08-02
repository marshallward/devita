#!/usr/bin/env python
# Playstation Vita System Object File dump
# Contact: Marshall Ward (marshall.ward@gmail.com)

import binascii
import os
import struct
import yaml

# SFO globals
HEADER_BYTES = 20

type_code = {
    'utf-8 Special Mode': 0x0004,
    'utf-8': 0x0204,
    'integer': 0x0404}

if os.path.exists('ptypes.yaml'):
    with open('ptypes.yaml', 'r') as f:
        ptypes = yaml.load(f)
else:
    ptypes = None

class sfo(object):
    
    #---
    def __init__(self, filename=None):
        if fname:
            self.filename = fname
            self.load(filename)
    
    
    #---
    def load(self, filename):
        sfo_file = open(filename, 'rb')
        
        #---
        # Parse header
        header_raw = sfo_file.read(HEADER_BYTES)
        header = struct.unpack('<4s4BIII', header_raw)
        
        self.file_signature = header[0]
        self.file_version = '.'.join([str(h) for h in header[1:5]])
        
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
        
        # Read past any padded space between the definition and name tables
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
                value = value_raw.rstrip('\x00')
            elif v_type == 0x0404:
                # Reverse index to read as little-endian
                # NOTE: Method for raw string to int?
                value_ascii = binascii.hexlify(value_raw[::-1])
                value = int(value_ascii, 16)
            else:
                print 'unknown format'
            
            param_values.append(value)
        
        self.params = dict(zip(param_names, param_values))
        
        sfo_file.close()
    
    
    #---
    def dump(self):
        print 'SFO File Signature:', self.file_signature
        print 'SFO File Version:', self.file_version
        
        for p in self.params:
            print "{}: {}".format(p, self.params[p])

    
    #---
    def write(self, fname):
        sfo_out = open(fname, 'wb')
        
        # Parameters seem to be sorted alphabetically 
        p_names = sorted(self.params)
        
        # Write SFO code
        sfo_out.write(self.file_signature)
        
        # Write version
        sfo_version = [int(i) for i in self.file_version.split('.')]
        sfo_version_raw = struct.pack('<4B', *sfo_version)
        sfo_out.write(sfo_version_raw)
        
        # Calculate addressing
        n_param = len(self.params)
        
        def_table_start = HEADER_BYTES
        def_table_bytes = 16 * n_param
        
        # Pack each param name as C-style string (with \x00 ending)
        name_table_start = def_table_start + def_table_bytes
        name_table_bytes = sum([(len(s) + 1) for s in self.params])
        
        data_table_start = name_table_start + name_table_bytes
        
        header = struct.pack('<III', name_table_start, data_table_start,
                                     n_param)
        sfo_out.write(header)
        
        # Write definition table entries
        # TODO: create a param class
        name_bytecount = 0
        data_bytecount = 0
        
        for p in p_names:
            p_type = type_code[ptypes[p]['type']]
            p_used = ptypes[p]['used']
            # For undefined parameters, fill in the data size
            if not p_used:
                p_used = len(self.params[p])
                if p_type in (0x0004, 0x0204):
                    # Add one for presumed string termination byte \x00
                    p_used = p_used + 1
            p_size = ptypes[p]['size']
            
            p_record = struct.pack('<HHIII', name_bytecount, p_type, p_used,
                                             p_size, data_bytecount)
            sfo_out.write(p_record)
            
            # Update bytecount
            name_bytecount = name_bytecount + (len(p) + 1)
            data_bytecount = data_bytecount + p_size
        
        # Write name table
        for p in p_names:
            sfo_out.write(p + '\x00')

        # Write data table
        for p in p_names:
            p_code = type_code[ptypes[p]['type']]
            if p_code in (0x0004, 0x0204):
                p_val = self.params[p]
                p_size = ptypes[p]['size']
                sfo_out.write(self.params[p]
                              + '\x00'*max(0, p_size - len(p_val)))
            elif p_code == 0x0404:
                val = struct.pack('<I', self.params[p])
                sfo_out.write(val)
            else:
                print 'Unsupported type'
        
        sfo_out.close()


#---
if __name__ == '__main__':
    
    # TODO: Read file from command line
    fname = 'param.sfo'
    test = sfo(fname)
    test.dump()
    test.write('test.sfo')
