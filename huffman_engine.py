#!/usr/bin/env python3
import huffman_io_engine as io
from bitarray import bitarray
import numpy as np
import os.path
import sys
import traceback

INDENT = "\t"

class Node:
    def __init__(self):
        self.left = None
        self.right = None
        self.freq = None
        self.label = "Node"

    def _print(self,recursion_depth):
        print(f"{INDENT*recursion_depth}label: {self.label}")
        print(f"{INDENT*recursion_depth}freq: {self.freq}")
        
        self.right._print(recursion_depth+1)
        self.left._print(recursion_depth+1)

    def generate_code(self,code):
        if type(self.right) == Leaf_node:
            setattr(self.right,"code",code+"1")
        elif not self.right is None:
            self.right.generate_code(code+"1")

        if type(self.left) == Leaf_node:
            setattr(self.left,"code",code+"0")
        elif not self.left is None:
            self.left.generate_code(code+"0")

    def get_code(self,cm):
        if not self.right is None:
            self.right.get_code(cm)
        if not self.left is None:
            self.left.get_code(cm)

class Leaf_node:
    def __init__(self,val,freq):
        self.val = val
        self.freq = freq

    def _print(self,recursion_depth):
        print(f"{INDENT*recursion_depth}{'-'*20}")
        print(f"{INDENT*recursion_depth}label: '{self.val}'")
        print(f"{INDENT*recursion_depth}freq: {self.freq}")
        print(f"{INDENT*recursion_depth}code: {self.code}")
        print(f"{INDENT*recursion_depth}{'-'*20}")

    def get_code(self,cm):
        cm.cm[self.val] = self.code

class Tree:
    def __init__(self,string):
        self._freq = freq_table(string)
        self.table = self._freq.table

    def build_tree(self):
        queue = [Leaf_node(k,v) for k,v in self.table.items()] # node priority queue

        while not len(queue) < 3:
            s1 = queue.pop()
            s2 = queue.pop()

            node = Node()
            if s1.freq < s1.freq:
                node.left = s1
                node.right = s2
            else:
                node.left = s2
                node.right = s1

            node.freq = sum([node.left.freq,node.right.freq])

            _append = False
            index = 0
            while index < len(queue):
                if queue[index].freq < node.freq:
                    queue.insert(index,node)
                    break

                index += 1
            else:
                _append = True

            if _append:
                queue.append(node)

        self.root = Node()
        self.root.label = "Root"
        self.root.freq = sum(self.table.values())
        
        self.root.right = queue[0]

        if not len(queue) == 1:
            self.root.left = queue[1]
            
        self.root.generate_code("")

    def get_code(self,cm):
        self.root.get_code(cm)

    def display(self):
        self.root._print(0)

class freq_table:
    def __init__(self,string):
        self.all_freq = {}
        self.sorted_freq = {}
        self.string = string
        self._init()

    def _init(self):
        for char in self.string:
            if not char in self.all_freq.keys():
                self.all_freq[char] = 1
            else:
                self.all_freq[char] += 1

        while self.all_freq:
            for k,v in self.all_freq.items():
                if v == max(self.all_freq.values()):
                    self.sorted_freq[k] = v
                    del self.all_freq[k]
                    break

    @property
    def table(self):
        return self.sorted_freq

class Char_map:
    def __init__(self):
        self.char_map = {}

    @property
    def cm(self):
        return self.char_map

######################################################################################

'''
structure of file:
    tree
    filler bits
    compressed text
    data byte
        amount of labels/characters
    data bytes
        1st 6 digits
            stores amount of bytes needed for max len code
        last 2 digits: 
            encoding (00=0=ascii, 01=1=utf8, 10=2=utf16, 11=3=utf32)
'''

def compress(infile, outfile=None):
    try:
        logger.log("info", f"Reading data from '{os.path.abspath(infile)}'")
        
        with open(infile, "r") as f:
            string = f.read()

        logger.log("info", f"Data read successfully; building Huffman Tree")

        tree = Tree(string) # contructs huffman tree recursively
        tree.build_tree()

        cm = Char_map()
        tree.get_code(cm)
        char_map = cm.cm # copies lookup table to separate object for encoding

        logger.log("info", "Tree constructed, building formatted binary stream")

        encoding = io._get_encoding(string)
        treedata, amount_of_chars, max_len_code = io._encode_tree(char_map, encoding)

        if verbose:
            tree.display()
            print("Encoding:", {
                "00": "ASCII",
                "01": "UTF-8",
                "10": "UTF-16",
                "11": "UTF-32"
            }[encoding])
        
        bitstring = "1" + "".join(char_map[i] for i in string)
        bitarr = bitarray(
            # tree data
            treedata +

            # actual encoded data
            [0 for _ in range(8-(len(bitstring) % 8))] + # filler bits
            list(map(int,bitstring)) + # compressed text

            # 2 data bytes
            [int(i) for i in amount_of_chars + 
             max_len_code + 
             encoding]
        )

        if outfile is None:
            outfile = os.path.splitext(infile)[0] + ".bin" # creates outfile destination if not provided
            
        if (not override and os.path.exists(outfile)): # warn user if file already exists
            io.warn_override_file(outfile, logger)

        logger.log("info", f"Writing to '{os.path.abspath(outfile)}'")

        if verbose:
            print("Compressed data:")
            
            if len(bitarr) <= 1000:
                print(("="*20)+">", bitarr, ("="*20)+">", sep="\n")
            else:
                print(("="*20)+">", bitarr[:500], "\n\t...\n" , bitarr[-500:], ("="*20)+">", sep="\n")
            
        with open(outfile,"wb+") as f:
            bitarr.tofile(f)
            
    except Exception as e:
        logger.log("error", "An unexpected error occurred: ", "".join(traceback.format_exception(*sys.exc_info())))

def decompress(infile, outfile=None):
    try:
        logger.log("info", f"Reading data from '{os.path.abspath(infile)}'")

        uncompressed = ""
        string = "".join(io._reformat_bin(list(map(str,np.fromfile(infile,"u1"))))) # reads int from file and converts it to binary

        logger.log("info", f"Data read successfully; constructing table for lookup.")

        string, data_bytes = string[:-16], string[-16:] # gets last 2 bytes from data
        tree, string, encoding = io._get_tree(string, data_bytes) # decodes tree data and returns rest of data

        logger.log("info", f"Table constructed; preparing string for decompression")

        if verbose:
            print("Lookup table generated:")
            io.display_dict(tree, cols=4, reverse=True)
            print("\nEncoding:", {
                "00": "ASCII",
                "01": "UTF-8",
                "10": "UTF-16",
                "11": "UTF-32"
            }[encoding])
            
        # gets rid of filler bits
        while not int(string[0]):
            string = string[1:]
        string = string[1:]

        # decodes from lookup
        while string:
            for p, code in enumerate(tree):
                if code[0] == string[:len(code[0])]:
                    uncompressed += code[1]
                    string = string[len(code[0]):]
                    break
            else: # in the case where character does not exist
                logger.log("fatal", "Error decoding - code not found in string; exiting.")

        if outfile is None:
            outfile = os.path.splitext(infile)[0] + ".txt" # creates outfile destination if not provided

        if (not override and os.path.exists(outfile)): # warns user if file already exists
            io.warn_override_file(outfile, logger)

        logger.log("info", f"Uncompressed string formed; writing to '{os.path.abspath(outfile)}'")

        if verbose:
            print("Uncompressed text:")
            
            if len(uncompressed) <= 1000:
                print(("="*20)+">", uncompressed, ("="*20)+">", sep="\n")
            else:
                print(("="*20)+">", uncompressed[:500], "\n\t...\n" , uncompressed[-500:], ("="*20)+">", sep="\n")
            
        with open(outfile, "w+") as f:
            f.write(uncompressed)

    except:
        logger.log("error", "An unexpected error occurred: ", "".join(traceback.format_exception(*sys.exc_info())))

def string_compress(string):
    pass

def string_decompress(string):
    pass
