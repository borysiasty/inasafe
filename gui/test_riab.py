"""
Disaster risk assessment tool developed by AusAid - **QGIS plugin test suite.**

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'tim@linfiniti.com'
__version__ = '0.2.0'
__date__ = '10/01/2011'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')

import unittest
import sys
import os

# Add parent directory to path to make test aware of other modules
pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(pardir)

from qgis.gui import QgsMapCanvas
from qgisinterface import QgisInterface
from PyQt4.QtGui import QWidget
from utilities_test import getQgisTestApp
from gui.riab import Riab

QGISAPP, CANVAS, IFACE, PARENT = getQgisTestApp()


class RiabTest(unittest.TestCase):
    """Test suite for Risk in a Box QGis plugin"""

    def test_load(self):
        """Risk in a Box QGis plugin can be loaded"""

        myParent = QWidget()
        myCanvas = QgsMapCanvas(myParent)
        myIface = QgisInterface(myCanvas)
        Riab(myIface)

    def test_setupI18n(self):
        """Gui translations are working."""

        myUntranslatedString = 'Show/hide Risk in a Box dock widget'
        myExpectedString = 'Tampilkan/hilangkan widget Risk in a Box'
        myParent = QWidget()
        myCanvas = QgsMapCanvas(myParent)
        myIface = QgisInterface(myCanvas)
        myRiab = Riab(myIface)
        myRiab.setupI18n('id')
        myTranslation = myRiab.tr(myUntranslatedString)
        myMessage = '\nTranslated: %s\nGot: %s\nExpected: %s' % (
                            myUntranslatedString,
                            myTranslation,
                            myExpectedString)
        assert myTranslation == myExpectedString, myMessage

    def test_ImpactFunctionI18n(self):
        """Library translations are working."""

        myUntranslatedString = 'Temporarily Closed'
        myExpectedString = 'Tydelik gesluit'  # afrikaans
        myParent = QWidget()
        myCanvas = QgsMapCanvas(myParent)
        myIface = QgisInterface(myCanvas)
        myRiab = Riab(myIface)
        myRiab.setupI18n('af')  # afrikaans
        # import this late so that i18n setup is already in place
        from storage.utilities import ugettext as _
        myTranslation = _(myUntranslatedString)
        myMessage = '\nTranslated: %s\nGot: %s\nExpected: %s' % (
                            myUntranslatedString,
                            myTranslation,
                            myExpectedString)
        assert myTranslation == myExpectedString, myMessage

        # This is part test and part demonstrator of how to reload riab
        # Now see if the same function is delivered for the function
        # Because of the way impact plugins are loaded in riab
        # (see http://effbot.org/zone/metaclass-plugins.htm)
        # lang in the context of the ugettext function in riab libs
        # must be imported late so that i18n is set up already
        del myRiab
        # reload all riab modules so that i18n get picked up afresh
        for myMod in sys.modules.values():
            try:
                if ('storage' in str(myMod) or
                   'impact' in str(myMod)):
                    print 'Reloading:', str(myMod)
                    reload(myMod)
            except:
                pass
        myRiab = Riab(myIface)
        myRiab.setupI18n('af')  # afrikaans
        myLang = os.environ['LANG']
        assert myLang == 'af'
        from impact_functions import get_plugins
        #myFunctions = get_plugins()
        #print myFunctions
        myFunctions = get_plugins('Tydelik gesluit')
        assert len(myFunctions) > 0

        # Test indonesian too
        myRiab.setupI18n('id')  # indonesian
        myExpectedString = 'Sementara Ditutup'
        myTranslation = _(myUntranslatedString)
        myMessage = '\nTranslated: %s\nGot: %s\nExpected: %s' % (
                            myUntranslatedString,
                            myTranslation,
                            myExpectedString)
        assert myTranslation == myExpectedString, myMessage

if __name__ == '__main__':
    unittest.main()
