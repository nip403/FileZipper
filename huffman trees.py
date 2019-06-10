from huffman_engine import encode_compressed,decode_compressed

string = "the quick brown fox jumped over the lazy dog"

def main(string):
    tree,compressed = encode_compressed(string)
    uncompressed = decode_compressed(tree)

if __name__ == "__main__":
    main(string)
