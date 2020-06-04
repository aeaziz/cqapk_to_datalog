class MalformedQuery(Exception):
    """
    Exception for malformed inputs
    """
    def __init__(self, string, data_type):
        super().__init__("%s is not a valid %s" % (string, data_type))


class NotSelfJoinFreeQuery(Exception):
    """
    Exception for queries that are not a sjfbcq
    """
    def __init__(self):
        super().__init__("The given query is not self-join free")


class CoNPComplete(Exception):
    """
    Exception used when CERTAINTY(q) is coNP-complete
    """
    def __init__(self):
        super().__init__("CERTAINTY(q) is coNP-complete for the given query")
