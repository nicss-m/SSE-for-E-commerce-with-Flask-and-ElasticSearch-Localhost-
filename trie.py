class TrieNode():
    def __init__(self):
        # Initialising one node for trie
        self.children = {}
        self.last = False
        self.freq = 0

class Trie():
    
    def __init__(self,min_freq,max_freq):
        self.total = 0
        self.count = 0
        self.limit = 7
        self.cur_min = 0
        self.root = TrieNode()
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.results,self.frequencies = [],[]

    def formTrie(self, items, min_len=1, max_len=10):

        # Forms a trie structure with the given set of strings
        # if it does not exists already else it merges the key
        # into it by extending the structure as required
        for key,freq in items:
            if len(key)<=max_len and len(key)>=min_len:
                self.insert(' '.join(key),freq)  # inserting one key to the trie.
            
    def frequency_check(self, freq, word):
        if self.count<self.limit:
            self.results.append(word)
            self.frequencies.append(freq)
            self.count+=1
        elif self.count==self.limit:
            self.cur_min = min(self.frequencies)
            self.count+=1
        else:
            if freq>self.cur_min:
                idx = self.frequencies.index(self.cur_min)
                self.frequencies[idx]=freq
                self.results[idx]=word
                self.cur_min = min(self.frequencies)         
            
    def insert(self, key, freq):
        if freq<self.min_freq:
            return False

        # Inserts a key into trie if it does not exist already.
        # And if the key is a prefix of the trie node, just
        # marks it as leaf node.
        node = self.root
        for a in key:
            if not node.children.get(a):
                node.children[a] = TrieNode()
            node = node.children[a]

        node.last = True
        if freq>self.max_freq:
            freq = self.max_freq
        node.freq = freq
        self.total+=1

    def suggestionsRec(self, node, word):

        # Method to recursively traverse the trie
        # and return a whole word.
        if node.last:
            self.frequency_check(node.freq,word)
            if self.cur_min==self.max_freq:
                return True

        for a, n in node.children.items():
            rs = self.suggestionsRec(n, word + a)
            if rs:
                return True

    def AutoSuggestions(self, key):

        # Returns all the words in the trie whose common
        # prefix is the given key thus listing out all
        # the suggestions for autocomplete.
        node = self.root

        for a in key:
            # no string in the Trie has this prefix
            if not node.children.get(a):
                return 0
            node = node.children[a]

        # If prefix is present as a word, but
        # there is no subtree below the last
        # matching node.
        if not node.children:
            return -1

        self.suggestionsRec(node, key)
        rs = self.results
        self.results,self.frequencies = [],[]
        self.cur_min,self.count = 0,0
        return rs