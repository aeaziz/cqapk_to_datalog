class MalformedQuery(Exception):
    def __init__(self, string, type):
        super().__init__("%s is not a valid %s" % (string, type))

class NotSelfJoinFreeQuery(Exception):
    def __init__(self):
        super().__init__("The given query is not self-join free")

class CoNPComplete(Exception):
    def __init__(self):
        super().__init__("CERTAINTY(q) is coNP-complete for the given query")