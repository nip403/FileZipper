#!/usr/bin/env python3
import os.path
import subprocess
import sys
import math

# used when -o flag is not set
def warn_override_file(file, logger):
    while True: 
        ans = input("Override file? (y/n): ")

        if ans.lower() == "n":
            logger.log("info", f"Can't allocate data to '{os.path.abspath(file)}'; exiting.")
            sys.exit()
        elif ans.lower() == "y":
            return

# pretty prints a dict as a table
def display_dict(d, cols=2, gap=4, reverse=False):  
    max_len = max([sum(len(j) for j in i) for i in d])
    
    for p,i in enumerate(d):
        key, val = i
        
        if reverse:
            key, val = val, key

        print(f"{repr(key)}: {val}{' '*(max_len-len(key)-len(val)+gap)}", end="\n" if not (p+1)%cols else "")

def formatsize(size): # formats bytes into readable format
    sizes = [
        "bytes",
        "KB",
        "MB",
        "GB",
        "TB"
    ]
    _size = 0

    while len(str(size)) > 3:
        size = math.ceil(size/1024)
        _size += 1

    return f"{round(size)}{sizes[_size]}"

# check if user has bitarray, if not tries to install with pip
def validate_bitarr():
    try:
        import bitarray
    except:
        logger.forcelog("warn", "Bitarray module not found. Trying pip")

        try:
            import pip
        except:
            logger.log("fatal", "Pip not found. Run code @ https://bootstrap.pypa.io/get-pip.py")

        logger.forcelog("info", "Pip module found, attempting to download and install bitarray")
        subprocess.call([sys.executable, "-m", "pip", "install", "bitarray"])

        try:
            import bitarray
            logger.forcelog("info", "Success: bitarray module present")
            return
        except:
            logger.forcelog("info", "Insufficient permissions to install bitarray, attempting administrative install")
            subprocess.call(["runas", "/user:Administrator", sys.executable, "-m pip install bitarray"])
        
    try:
        import bitarray
        logger.forcelog("info", "Success: bitarray module present")
    except:
        logger.log("fatal", "Unexpected error, bitarray module did not install; exiting.")

#### #### #### #### COMPRESSION #### #### #### ####
def _reformat_bin(arr, digits=8): # converts an array of ints to binary
    arr = list(map(int,arr))
    out = []

    for byte in arr:
        b = ""

        for i in reversed(range(digits)): # if 2**digits - 1 > byte: data is lost
            if byte >= 2**i: # checks if binary digit <= the number
                byte -= 2**i
                b += "1"
            else:
                b += "0"

        out.append(b)

    return out

def _get_encoding(string):
    '''
    0 = ASCII
    1 = UTF-8
    2 = UTF-16 (2 bytes)
    3 = UTF-32 (4 bytes)
    Unicode Standard 12.1 - 137,929 maximum codes = 3 bytes

    last 2 bits found on every file
    '''
    
    mode = 0
    max_bits = [127, 255, 65535, 16777215]#4294967295]

    # finds minimum amount of bytes necessary to display string
    for c in string:
        for i,b in enumerate(max_bits):
            if ord(c) <= b:
                if mode < i:
                    mode = i
                break # updates mode until everything in the string has satisfied the encoding

    return _reformat_bin([mode], digits=2)[0] # reformats the mode (int from 0-3) into 2 bit binary; reformat func returns a list

def _encode_tree(cmap, string_encoding): # encodes the huffman tree data into a binary stream
    char_bit_length = {
        "00": 8,  # ASCII
        "01": 8,  # UTF-8
        "10": 16, # UTF-16
        "11": 24  # UTF-32 - currently maximum code only uses 3 bytes, max 4
    }[string_encoding]

    # amount of different mappings
    amount_of_chars = _reformat_bin([len(cmap.keys())])[0]

    # the largest length of binary code to represent a character
    max_len_code_decimal = max(map(len,cmap.values()))
    max_len_code = _reformat_bin([max_len_code_decimal], digits=6)[0]

    # rounds up to the nearest byte
    len_code_bytes = max_len_code_decimal//8 + 1
    
    # output bytestream
    tree_bin_data = ""

    '''
    format of each individual entry:
    1. character bytes (length in bytes determined by char_bit_length)
    2. data byte, contains info of how many bits to skip whilst reading code byte(s), as there may be uneven amount
        It is a waste of space, as the max number of bits to skip is 7
        only if the byte size is dynamic - will have to optimise
    3. code byte(s) (length determined by max_len_code)

    [char data (1-3 bytes)][read data (1 byte)][code data (any size, scales to size of tree)]
    '''
    
    # loops through lookup table (tree)
    for char, code in cmap.items():
        # char bytes
        # converts char into unicode int and then binary, with a byte length of char_bit_length/8
        tree_bin_data += _reformat_bin([str(ord(char))], digits=char_bit_length)[0]

        # data byte
        # finds out amount of digits to skip when reading code bytes
        _fill_space = (len_code_bytes*8)-len(code)
        tree_bin_data += _reformat_bin([_fill_space])[0]

        # code bytes
        # writes literal code generated by huffman tree
        tree_bin_data += ("0" * _fill_space) + code
    
    # returns binary data, other info for debugging and finalising data to be written to file
    return list(map(int,tree_bin_data)), amount_of_chars, max_len_code

#### #### #### #### DECOMPRESSION #### #### #### ####
def _bin_to_dec(binary): # converts a binary number (str) into an int
    current_pow_2 = 0
    running_sum = 0

    binary = list(binary)

    while len(binary):
        running_sum += int(binary.pop()) * (2**current_pow_2)
        current_pow_2 += 1

    return running_sum

def _get_tree(string, data_bytes): # decodes binary tree data from file data and generates lookup table
    amount_of_labels, max_len_code, encoding = data_bytes[:8], _bin_to_dec(data_bytes[8:14]), data_bytes[14:]
    tree = {}
    
    char_byte_length = {
        "00": 1, # ASCII
        "01": 1, # UTF-8
        "10": 2, # UTF-16
        "11": 3  # UTF-32 - currently maximum code only uses 3 bytes, max 4
    }[encoding]

    # converts bitstream into bytearray: "011010101101000011111101" => ["01101010", "11010000", "11111101"]
    bytearr = [string[i:i+8] for i in range(0, len(string)-1, 8)]

    # note that bytearr/string is the tree data as well as the actual compressed text
    # therefore function returns tree and the rest of the data, which is then decoded

    for _ in range(_bin_to_dec(amount_of_labels)):
        # separates char by known length - set by the encoding before compression
        char, bytearr = "".join(bytearr[:char_byte_length]), bytearr[char_byte_length:]
        data_byte = bytearr.pop(0)
        
        code_bytes_amount = max_len_code//8 + 1
        code, bytearr = "".join(bytearr[:code_bytes_amount]), bytearr[code_bytes_amount:]

        # fetch actual code by removing filler bytes
        code = code[_bin_to_dec(data_byte):]

        # map
        tree[code] = chr(_bin_to_dec(char))
        
    # returns encoding for verbose mode
    # sorts tree by longest code first
    return sorted(tree.items(), key=lambda p: len(p[0]), reverse=True), "".join(bytearr), encoding

def is_bin(string): # checks if string represents binary
    return all(i in "01" for i in string)
