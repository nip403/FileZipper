# Nipzip
My implementation of a compression algorithm written in Python 3.x using [Huffman Coding](https://en.wikipedia.org/wiki/Huffman_coding), which is commonly used for lossless compression. 

Nipzip compresses and decompresses text to binary and vice versa.

## Usage
```
Usage: py nipzip.py [options]

    Notes:
        - Can only use one option at a time
        - If using string mode, delimit string with quotes if it contains a space


Options:
  -h, --help          show this help message and exit

  File Options:
    -o, --override    Automatically overrides existing file if destination
                      file has content instead of prompting
    --source=SOURCE   Full path to source file (e.g. C:\Users\file.txt,
                      ..\tmp\binary.bin)
    --dest=DEST       Full path to destination file - if not provided, will
                      create a file with the same name as source file in the
                      same directory

  String Options:
    --compress=TEXT   Encodes a string and outputs binary string
    --decompress=BIN  Decodes a string and outputs decompressed string

  Debug Options:
    -v, --verbose     Verbose mode: display compressed and uncompressed data
    -d, --debug       Debug mode: display logging info
```

### Dependencies
- Python 3.6 or older
- _bitarray_ module (`pip install bitarray`)

