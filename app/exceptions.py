########################
# Exception Hierarchy  #
########################

class CalculatorError(Exception):
    pass


class ValidationError(CalculatorError):
    pass


class OperationError(CalculatorError):
    pass


class ConfigurationError(CalculatorError):
    pass
