import numpy as np

class Node:
    def __init__(self):
        self.left = None
        self.right = None
        self.freq = None

    def print(self,recursion_depth):
        print(f"{'  '*recursion_depth}label: None")
        print(f"{'  '*recursion_depth}freq: {self.freq}")
        
        self.right.print(recursion_depth+1)
        self.left.print(recursion_depth+1)

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

    def print(self,recursion_depth):
        print(f"{'  '*recursion_depth}label: '{self.val}'")
        print(f"{'  '*recursion_depth}freq: {self.freq}")
        print(f"{'  '*recursion_depth}code: {self.code}")

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
        self.root.right = queue[0]

        if not len(queue) == 1:
            self.root.left = queue[1]
            
        self.root.generate_code("")

    def get_code(self,cm):
        self.root.get_code(cm)

    def display_tree(self):
        self.root.print(0)

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

def encode_compressed(string,write_to_file=True,filename="bin_encoded.bin"):
    tree = Tree(string)
    tree.build_tree()

    cm = Char_map()
    tree.get_code(cm)
    char_map = cm.cm

    compressed = ""
    for i in string:
        compressed += char_map[i]

    if write_to_file:
        open(filename,"wb").close()
        with open(filename,"ab+") as f:
            f.write(bytes(list(map(int,compressed))))
            f.close()

    return tree,compressed

def decode_compressed(tree,string="bin_encoded.bin",is_file=True):
    uncompressed = ""
    current = tree.root

    if is_file:
        string = "".join(list(map(str,np.fromfile(string,"u1"))))
               
    for i in string:
        if i == "1":
            current = current.right
        else:
            current = current.left

        if type(current) == Leaf_node:
            uncompressed += current.val
            current = tree.root

    return uncompressed
