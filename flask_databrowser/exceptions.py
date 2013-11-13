class ValidationError(Exception):

    pass

    #def __init__(self, message="", args=None):
        #super(ValidationError, self).__init__(message)
        #self.args = args


class InvalidArgumentError(Exception):
    pass