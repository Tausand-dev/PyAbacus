#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class BaseError(Exception):
    def __init__(self, message):
        self.message = str(message)

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message

class CheckSumError(BaseError):
    """ An error occurred while doing check sum. """

    def __init__(self):
        super(CheckSumError, self).__init__("An error occurred while doing check sum.")

class AbacusError(BaseError):
    """ An unexpected error occurred. """

    def __init__(self, message = ""):
        super(AbacusError, self).__init__("An unexpected error occurred " + message)

class TimeOutError(BaseError):
    """ A time out error occurred """

    def __init__(self, message = ""):
        super(TimeOutError, self).__init__("A timeout error occurred " + message)

class InvalidValueError(BaseError):
    """ The selected value is not valid """

    def __init__(self, message = ""):
        super(InvalidValueError, self).__init__("The selected value is not valid" + message)
