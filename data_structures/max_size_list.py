class MaxSizeList(list):
    def __init__(self, max_len):
        super(MaxSizeList, self).__init__()
        self.max_len = max_len

    def append(self, element):
        if len(self) == self.max_len:
            self.__delitem__(0)
        super(MaxSizeList, self).append(element)
