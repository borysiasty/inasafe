"""
InaSAFE Disaster risk assessment tool by AusAid - **Error Message example.**

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.
"""

__author__ = 'tim@linfiniti.com'
__revision__ = '$Format:%H$'
__date__ = '27/05/2013'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')

import sys
import os
import traceback
from safe.messaging import (
    Message,
    ErrorMessage,
    ImportantText,
    Text,
    Paragraph)
from third_party.pydispatch import dispatcher


DYNAMIC_MESSAGE_SIGNAL = 'ImpactFunctionMessage'


class SafeError(Exception):
    """Base class for all SAFE messages that propogates ErrorMessages."""
    def __init__(self, message, error_message=None):
        #print traceback.format_exc()
        Exception.__init__(self, message)

        if error_message is not None:
            self.error_message = error_message
        else:
            self.error_message = ErrorMessage(
                message.message, traceback=traceback.format_exc())


def error_creator1():
    """Simple function that will create an error."""
    raise IOError('File could not be read.')


def error_creator2():
    """Simple function that will extend an error and its traceback."""
    try:
        error_creator1()
    except IOError, e:
        e.args = (e.args[0] + '\nCreator 2 error',)  # Tuple dont remove last ,
        raise


def error_creator3():
    """Raise a safe style error."""
    try:
        error_creator2()
    except IOError, e:
        #e.args = (e.args[0] + '\nCreator 3 error',)  # Tuple dont remove
        # last ,
        raise SafeError(e)


def error_creator4():
    """Raise a safe style error."""
    try:
        error_creator3()
    except SafeError, e:
        e.error_message.problems.append('Creator 4 error')
        raise


def error_creator5():
    """Raise a safe style error and append a full message."""
    try:
        error_creator4()
    except SafeError, e:
        message = ErrorMessage(
            'Creator 5 problem',
            detail=Message(
                Paragraph('Could not', ImportantText('call'), 'function.'),
                Paragraph('Try reinstalling your computer with windows.')),
            suggestion=Message(ImportantText('Important note')))
        e.error_message.append(message)
        raise

if __name__ == '__main__':
    # best practice non safe style errors
    #try:
    #    error_creator2()
    #except IOError, e:
    #    #print e
    #    tb = traceback.format_exc()
    #    print tb

    # Safe style errors
    try:
        error_creator5()
    except SafeError, e:
        #print e
        #tb = traceback.format_exc()
        #print tb
        print e.error_message.to_text()

