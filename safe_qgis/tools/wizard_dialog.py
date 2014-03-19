# coding=utf-8
"""
InaSAFE Disaster risk assessment tool by AusAid **GUI InaSAFE Wizard Dialog.**

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

.. todo:: Check raster is single band

"""

__author__ = 'qgis@borysjurgiel.pl'
__revision__ = '$Format:%H$'
__date__ = '21/02/2011'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')

import logging
import re
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QListWidgetItem, QPixmap

# from third_party.odict import OrderedDict

from safe_qgis.safe_interface import InaSAFEError
from safe_qgis.ui.wizard_dialog_base import Ui_WizardDialogBase
from safe_qgis.utilities.keyword_io import KeywordIO
from safe_qgis.utilities.utilities import (
    get_error_message,
    is_point_layer,
    is_polygon_layer,
    is_raster_layer)


LOGGER = logging.getLogger('InaSAFE')

#
#
#
#
#
#
#
#
#
#
#
#
#

# A TEMPORARY CONSTANTS UNTIL safe.metadata IS READY
from PyQt4.QtGui import QApplication


def text(constant):
    """Find a constant by name and return its value.
    Usable for finding constants like volcano_text, when the name
    is composed dybamically from a keyword and a suffix

    :param constant: The name of the constant to look for
    :type constant: string

    :returns: The value of the constant or red error message
    :rtype: string

    """
    try:
        return eval(constant)
    except:
        # raise Exception('MISSING CONSTANT: %s' % constant)
        return '<b>MISSING CONSTANT: %s</b>' % constant


# constants for categories
category_question = QApplication.translate(
    'safe_metadata',
    'By following the simple steps in this wizard, you can assign '
    'keywords to your layer: <b>%s</b>. First you need to define '
    'the category of your layer.')   # (layer name)

hazard_name = 'Hazard'
hazard_text = QApplication.translate(
    'safe_metadata',
    'A <b>hazard</b> layer represents '
    'something that will impact on the people or infrastructure '
    'in an area. For example; flood, earthquake, tsunami and  '
    'volcano are all examples of hazards.')

exposure_name = 'Exposure'
exposure_text = QApplication.translate(
    'safe_metadata',
    'An <b>exposure</b> layer represents '
    'people, property or infrastructure that may be affected '
    'in the event of a flood, earthquake, volcano etc.')

aggregation_name = 'Aggregation'
aggregation_text = QApplication.translate(
    'safe_metadata',
    'An <b>aggregation</b> layer represents '
    'regions you can use to summarise the results by. For '
    'example, we might summarise the affected people after'
    'a flood according to city districts.')

# constants for hazards
hazard_question = QApplication.translate(
    'safe_metadata',
    'What kind of hazard does this '
    'layer represent? The choice you make here will determine '
    'which impact functions this hazard layer can be used with. '
    'For example, if you choose <b>flood</b> you will be '
    'able to use this hazard layer with impact functions such '
    'as <b>flood impact on population</b>.')

flood_name = 'Flood'
flood_text = QApplication.translate(
    'safe_metadata',
    'A <b>flood</b> describes the inundation of land that is '
    'normally dry by a large amount of water. '
    'For example: A <b>flood</b> can occur after heavy rainfall, '
    'when a river overflows its banks or when a dam breaks. '
    'The effect of a <b>flood</b> is for land that is normally dry '
    'to become wet.')
tsunami_name = 'Tsunami'
tsunami_text = QApplication.translate(
    'safe_metadata',
    'A <b>tsunami</b> describes a large ocean wave or series or '
    'waves usually caused by an under water earthquake or volcano.'
    'A <b>tsunami</b> at sea may go unnoticed but a <b>tsunami</b> '
    'wave that strikes land may cause massive destruction and '
    'flooding.')
earthquake_name = 'Earthquake'
earthquake_text = QApplication.translate(
    'safe_metadata',
    'An <b>earthquake</b> describes the sudden violent shaking of the '
    'ground that occurs as a result of volcanic activity or movement '
    'in the earth\'s crust.')
tephra_name = 'Tephra'
tephra_text = QApplication.translate(
    'safe_metadata',
    '<b>Tephra</b> describes the material, such as rock fragments and '
    'ash particles ejected by a volcanic eruption.')
volcano_name = 'Volcano'
volcano_text = QApplication.translate(
    'safe_metadata',
    'A <b>volcano</b> describes a mountain which has a vent through '
    'which rock fragments, ash, lava, steam and gases can be ejected '
    'from below the earth\'s surface. The type of material '
    'ejected depends on the type of <b>volcano</b>.')

# constants for exposures
exposure_question = QApplication.translate(
    'safe_metadata',
    'What kind of exposure does this '
    'layer represent? The choice you make here will determine '
    'which impact functions this exposure layer can be used with. '
    'For example, if you choose <b>population</b> you will be '
    'able to use this exposure layer with impact functions such '
    'as <b>flood impact on population</b>.')

population_name = 'Population'
population_text = QApplication.translate(
    'safe_metadata',
    'The <b>population</b> describes the people that might be '
    'exposed to a particular hazard.')
structure_name = 'Structure'
structure_text = QApplication.translate(
    'safe_metadata',
    'A <b>structure</b> can be any relatively permanent man '
    'made feature such as a building (an enclosed structure '
    'with walls and a roof) or a telecommunications facility or a '
    'bridge.')
road_name = 'Road'
road_text = QApplication.translate(
    'safe_metadata',
    'A <b>road</b> is a defined route used by a vehicle or people to '
    'travel between two or more points.')

# constants for units
unit_question = QApplication.translate(
    'safe_metadata',
    'You have selected <b>%s</b> '
    'for this <b>%s</b> layer type. We need to know what units the '
    'data are in. For example in a raster layer, each cell might '
    'represent depth in metres or depth in feet. If the dataset '
    'is a vector layer, each polygon might represent an inundated '
    'area, while ares with no polygon coverage would be assumed '
    'to be dry.')   # (subcategory, category)

depth_metres_name = 'Metres'
depth_metres_text = QApplication.translate(
    'safe_metadata',
    '<b>metres</b> are a metric unit of measure. There are 100 '
    'centimetres in 1 metre. In this case <b>metres</b> are used to '
    'describe the water depth.')
depth_feet_name = 'Feet'
depth_feet_text = QApplication.translate(
    'safe_metadata',
    '<b>Feet</b> are an imperial unit of measure. There are 12 '
    'inches in 1 foot and 3 feet in 1 yard. '
    'In this case <b>feet</b> are used to describe the water depth.')
wetdry_name = 'Wet/Dry'
wetdry_text = QApplication.translate(
    'safe_metadata',
    'This is a binary description for an area. The area is either '
    '<b>wet</b> (affected by flood water) or <b>dry</b> (not affected '
    'by flood water). This unit does not describe how <b>wet</b> or '
    '<b>dry</b> an area is.')
mmi_text = QApplication.translate(
    'safe_metadata',
    'The <b>Modified Mercalli Intensity (MMI)</b> scale describes '
    'the intensity of ground shaking from a earthquake based on the '
    'effects observed by people at the surface.')
notset_text = QApplication.translate(
    'safe_metadata',
    '<b>Not Set</b> is the default setting for when no units are '
    'selected.')
kgm2_text = QApplication.translate(
    'safe_metadata',
    '<b>Kilograms per square metre</b> describes the weight in '
    'kilograms by area in square metres.')
count_text = QApplication.translate(
    'safe_metadata',
    '<b>Count</b> is the number of features.')
density_text = QApplication.translate(
    'safe_metadata',
    '<b>Density</b> is the number of features within a defined '
    'area. For example <b>population density</b> might be measured '
    'as the number of people per square kilometre.')
road_type_name = 'Road Type'
road_type_text = 'Road type depends on its surface, width and purpose.'


flood_metres_question = 'flood depth in meters'
flood_feet_question = 'flood depth in feet'
flood_wetdry_question = 'flood extent as wet/dry'
tsunami_metres_question = 'flood depth in meters'
tsunami_feet_question = 'flood depth in feet'
tsunami_wetdry_question = 'flood extent as wet/dry'
earthquake_question = 'earthquake intensity in MMI'
tephra_kgm2_question = 'tephra intensity in kg/m<sup>2</sup>'
population_number_question = 'the number of people'
population_density_question = 'people density in people/km<sup>2</sup>'
road_roadclass_question = 'type for your road'

# constants for field selection
field_question_values = QApplication.translate(
    'safe_metadata',
    'You have selected a <b>%s %s</b> layer measured in '
    '<b>%s</b>, and the selected layer is vector layer. Please '
    'select the attribute in this layer that represents %s.')
    # (category, subcategory, unit, unit next question))

#field_question_no_values = QApplication.translate(
    #'safe_metadata',
    #'You have selected a <b>%s %s</b> layer, and it is a vector '
    #'layer. Which column contains the <b>%s</b>?')
    ## (category, subcategory, unit next question)

field_question_aggregation = QApplication.translate(
    'safe_metadata',
    'You have selected an aggregation layer, and it is a vector '
    'layer. Please select the attribute in this layer that '
    'represents names of the aggregation areas.')

# constants for classift tab
classify_question = QApplication.translate(
    'safe_metadata',
    'You have selected <b>%s %s</b> measured in <b>%s</b> categorical '
    'unit, and the data column is <b>%s</b>. Below on the left you '
    'can see all unique values found in that column. Please drag them '
    'to the right panel in order to classify them to appropriate '
    'categories.')   # (subcategory, category, unit, field)


# A TEMPORARY CLASS UNTIL THE REAL API IS READY
class FakeAPI():
    def categories_for_layer(self, layer_type, data_type):
        return ['hazard', 'exposure', 'aggregation']

    def subcategories_for_layer(self, layer_type, data_type, category):
        if category == 'hazard':
            return ['flood', 'tsunami', 'earthquake', 'tephra', 'volcano']
        elif category == 'exposure':
            return ['population', 'structure', 'road']
        else:
            return []

    def units_for_layer(self, layer_type, data_type, subcategory):
        return[
        # First kind of unit
        {
            'id': 'wetdry',
            'constraint': 'categorical',
            'default_category': 'wet',
            'classes': [
                {
                    'name': 'wet',
                    'description': 'Water above ground height.',
                    'string_defaults': ['wet', '1', 'YES', 'y', 'yes'],
                    'numeric_default_min': 1,
                    'numeric_default_max': 9999999999,
                    'optional': True
                },
                {
                    'name': 'dry',
                    'description': 'No water above ground height.',
                    'string_defaults': ['dry', '0', 'No', 'n', 'no'],
                    'numeric_default_min': 0,
                    'numeric_default_max': 0.9999999999,
                    'optional': True
                }
            ]
        },
        # Second kind of unit
        {
            'id': 'depth_metres',
            'constraint': 'continuous',
            'default_attribute': 'depth'  # applies to vector only
        },
        {
            'id': 'depth_feet',
            'constraint': 'continuous',
            'default_attribute': 'depth'  # applies to vector only
        },
        # Third kind of unit
        {
            'id': 'road_type',
            'constraint': 'unique values',
            'default_attribute': 'type'  # only applies to vector
        }
        ]

#
#
#
#
#
#
#
#
#
#
#
#
#

# Constants: tab numbers for steps
step_category = 1
step_subcategory = 2
step_unit = 3
step_field = 4
step_classify = 5
step_source = 6
step_title = 7


class WizardDialog(QtGui.QDialog, Ui_WizardDialogBase):
    """Dialog implementation class for the InaSAFE keywords wizard."""

    def __init__(self, parent, iface, dock=None, layer=None):
        """Constructor for the dialog.

        .. note:: In QtDesigner the advanced editor's predefined keywords
           list should be shown in english always, so when adding entries to
           cboKeyword, be sure to choose :safe_qgis:`Properties<<` and untick
           the :safe_qgis:`translatable` property.

        :param parent: Parent widget of this dialog.
        :type parent: QWidget

        :param iface: Quantum GIS QGisAppInterface instance.
        :type iface: QGisAppInterface

        :param dock: Dock widget instance that we can notify of changes to
            the keywords. Optional.
        :type dock: Dock
        """

        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle('InaSAFE')
        # Note the keys should remain untranslated as we need to write
        # english to the keywords file.

        # Save reference to the QGIS interface and parent
        self.iface = iface
        self.parent = parent
        self.dock = dock

        self.layer = layer or self.iface.mapCanvas().currentLayer()
        self.layer_type = is_raster_layer(self.layer) and 'raster' or 'vector'
        if self.layer_type == 'vector':
            if is_point_layer(self.layer):
                self.data_type = 'point'
            elif is_polygon_layer(self.layer):
                self.data_type = 'polygon'
            else:
                self.data_type = 'line'
        else:
            self.data_type = None

        self.kw_api = FakeAPI()

        # Set widgets on the first tab
        self.lblSelectCategory.setText(
            category_question % self.layer.name())

        for category in self.kw_api.categories_for_layer(
                self.layer_type, self.data_type):
            item = QListWidgetItem(text('%s_name' % category),
                                        self.lstCategories)
            item.setData(QtCore.Qt.UserRole, category)
            self.lstCategories.addItem(item)
        self.lblDescribeCategory.setText('')
        self.lblIconCategory.setText('')

        self.pbnBack.setEnabled(False)
        self.pbnNext.setEnabled(False)

        self.treeClasses.itemChanged.connect(self.update_dragged_item_flags)
        self.pbnCancel.released.connect(self.reject)

        self.go_to_step(1)

    def selected_category(self):
        """Obtain the category selected by user.

        :returns: keyword of the selected category
        :rtype: string or None
        """
        item = self.lstCategories.currentItem()
        if item:
            return item.data(QtCore.Qt.UserRole)
        else:
            return None

    def selected_subcategory(self):
        """Obtain the subcategory selected by user.

        :returns: keyword of the selected subcategory
        :rtype: string or None
        """
        item = self.lstSubcategories.currentItem()
        if item:
            return item.data(QtCore.Qt.UserRole)
        else:
            return None

    def selected_unit(self):
        """Obtain the unit selected by user.

        :returns: keyword of the selected unit
        :rtype: string or None
        """
        item = self.lstUnits.currentItem()
        if item:
            return item.data(QtCore.Qt.UserRole)
        else:
            return None

    def selected_unit_details(self):
        """Obtain details of the unit selected by user.

        :returns: details of the selected unit
        :rtype: dict or None
        """
        item = self.lstUnits.currentItem()
        try:
            return eval(item.data(QtCore.Qt.UserRole+1))
        except:
            return None

    def selected_field(self):
        """Obtain the field selected by user.

        :returns: keyword of the selected field
        :rtype: string or None
        """
        item = self.lstFields.currentItem()
        if item:
            return item.text()
        else:
            return None

    def selected_mapping(self):
        """Obtain the value-to-class mapping set by user.

        :returns: the complete mapping as a dict of lists
        :rtype: dict
        """
        value_map = {}
        tree_clone = self.treeClasses.invisibleRootItem().clone()
        for tree_branch in tree_clone.takeChildren():
            value_list = []
            for tree_leaf in tree_branch.takeChildren():
                value_list += [tree_leaf.text(0)]
            if value_list:
                value_map[tree_branch.text(0)] = value_list
        return value_map

    def update_dragged_item_flags(self, item, column):
        """A slot executed when thee item change. Check if it looks like
        an item  dragged from QListWidget to QTreeWidget and disable the
        drop flag. For some reasons the flag is set when dragging.
        """
        if int(item.flags() & QtCore.Qt.ItemIsDropEnabled) \
                and int(item.flags() & QtCore.Qt.ItemIsDragEnabled):
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsDropEnabled)

    # prevents actions being handled twice
    @pyqtSignature('')
    def on_lstCategories_itemSelectionChanged(self):
        """Automatic slot executed when category change. Set description label
           and subcategory widgets according to the selected category
        """
        self.lstSubcategories.clear()

        category = self.selected_category()
        # Exit if no selection
        if not category:
            return

        # Set description label
        self.lblDescribeCategory.setText(text('%s_text' % category))
        self.lblIconCategory.setPixmap(
            QPixmap(':/plugins/inasafe/keyword-category-%s.svg'
                    % (category or 'notset')))

        # Enable the next button
        self.pbnNext.setEnabled(True)

    def on_lstSubcategories_itemSelectionChanged(self):
        """Automatic slot executed when subcategory change. Set description
          label and unit widgets according to the selected category
        """
        self.lstUnits.clear()

        subcategory = self.selected_subcategory()
        # Exit if no selection
        if not subcategory:
            return

        # Set description label
        self.lblDescribeSubcategory.setText(text('%s_text' % subcategory))
        self.lblIconSubcategory.setPixmap(QPixmap(
            ':/plugins/inasafe/keyword-subcategory-%s.svg'
            % (subcategory or 'notset')))

        # Enable the next button
        self.pbnNext.setEnabled(True)

    def on_lstUnits_itemSelectionChanged(self):
        """Automatic slot executed when unit change. Set description label
           and field widgets according to the selected category
        """
        self.lstFields.clear()

        unit = self.selected_unit()
        # Exit if no selection
        if not unit:
            return
        self.lblDescribeUnit.setText(text('%s_text' % unit))

        # Enable the next button
        self.pbnNext.setEnabled(True)

    def on_lstFields_itemSelectionChanged(self):
        """Automatic slot executed when field change.
           Unlocks the Next button.
        """
        self.treeClasses.clear()

        field = self.selected_field()
        # Exit if no selection
        if not field:
            return

        fields = self.layer.dataProvider().fields()
        field_type = fields.field(field).typeName()
        field_idx = fields.indexFromName(self.selected_field())
        unique_values = self.layer.uniqueValues(field_idx)[0:48]
        unique_values_str = [i and unicode(i) or 'NULL' for i in unique_values]
        if unique_values != self.layer.uniqueValues(field_idx):
            unique_values_str += ['...']
        desc = '<br/>%s: %s<br/><br/>' % (self.tr('Field type'), field_type)
        desc += self.tr('Unique values: %s') % ', '.join(unique_values_str)
        self.lblDescribeField.setText(desc)

        # Enable the next button
        self.pbnNext.setEnabled(True)

    def on_leTitle_textChanged(self):
        """Automatic slot executed when the title change.
           Unlocks the Next button.
        """
        # Enable the next button
        self.pbnNext.setEnabled(bool(self.leTitle.text()))

    def update_subcategory_tab(self):
        """Set widgets on the Subcategory tab
        """
        category = self.selected_category()
        self.lstSubcategories.clear()
        self.lstUnits.clear()
        self.lblDescribeSubcategory.setText('')
        self.lblIconSubcategory.setPixmap(QPixmap())
        self.lblSelectSubcategory.setText(text('%s_question' % category))
        for i in self.kw_api.subcategories_for_layer(
                self.layer_type, self.data_type, category):
            item = QListWidgetItem(text('%s_name' % i), self.lstSubcategories)
            item.setData(QtCore.Qt.UserRole, i)
            self.lstSubcategories.addItem(item)

    def update_unit_tab(self):
        """Set widgets on the Unit tab
        """
        category = self.selected_category()
        subcategory = self.selected_subcategory()
        self.lblSelectUnit.setText(
            unit_question % (subcategory, category))
        self.lblDescribeUnit.setText('')
        self.lstUnits.clear()
        self.lstFields.clear()
        for i in self.kw_api.units_for_layer(
                self.layer_type, self.data_type, subcategory):
            item = QListWidgetItem(text('%s_name' % i['id']), self.lstUnits)
            item.setData(QtCore.Qt.UserRole, i['id'])
            item.setData(QtCore.Qt.UserRole+1, unicode(i))
            self.lstUnits.addItem(item)

    def update_field_tab(self):
        """Set widgets on the Field tab (lblSelectField and lstFields)
        """
        category = self.selected_category()
        subcategory = self.selected_subcategory()
        unit = self.selected_unit()
        unit_details = self.selected_unit_details()
        if subcategory and unit:
            next_question = text('%s_%s_question' % (subcategory,
                                                     unit))
        else:
            next_question = self.tr('<b><font color="red">ERROR! Missing '
                                    'subcategory or unit!</font></b>')

        if category == 'aggregation':
            question_text = field_question_aggregation
#        elif unit_details and unit_details['constraint'] == 'unique values':
#            # continuous or categorical data
#            question_text = field_question_no_values % (
#                category, subcategory, next_question)
        else:
            # unique values, continuous or categorical data
            question_text = field_question_values % (category,
                                                     subcategory,
                                                     unit,
                                                     next_question)
        self.lblSelectField.setText(question_text)
        self.lstFields.clear()

        for field in self.layer.dataProvider().fields():
            field_name = field.name()
            item = QListWidgetItem(field_name, self.lstFields)
            item.setData(QtCore.Qt.UserRole, field_name)
            if unit_details and unit_details['constraint'] == 'continuous':
                # For continuous data, gray out id, gid, fid and text fields
                field_type = field.type()
                if field_type > 9 or re.match('.{0,2}id$', field_name, re.I):
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEnabled)
        self.lblDescribeField.clear()

    def update_classify_tab(self):
        """Set widgets on the Classify tab
        """
        category = self.selected_category()
        subcategory = self.selected_subcategory()
        unit_details = self.selected_unit_details()
        default_classes = unit_details['classes']
        field = self.selected_field()
        field_idx = self.layer.dataProvider().fields().indexFromName(
            self.selected_field())
        field_type = self.layer.dataProvider().fields()[field_idx].type()
        self.lblClassify.setText(classify_question %
                                (subcategory, category,
                                 unit_details['id'], field.upper()))

        # Assign unique values to classes
        unassigned_values = list()
        assigned_values = dict()
        for cls in default_classes:
            assigned_values[cls['name']] = list()
        for val in self.layer.uniqueValues(field_idx):
            val_str = val and unicode(val) or 'NULL'
            assigned = False
            for cls in default_classes:
                if (field_type > 9 and val_str in cls['string_defaults']) \
                        or (field_type < 10
                            and val >= cls['numeric_default_min']
                            and val <= cls['numeric_default_max']):
                    assigned_values[cls['name']] += [val_str]
                    assigned = True
            if not assigned:
                # add to unassigned values list otherwise
                unassigned_values += [val_str]

        # Populate the unique vals list
        self.lstUniqueValues.clear()
        for val in unassigned_values:
            list_item = QtGui.QListWidgetItem(self.lstUniqueValues)
            list_item.setFlags(QtCore.Qt.ItemIsEnabled |
                               QtCore.Qt.ItemIsSelectable |
                               QtCore.Qt.ItemIsDragEnabled)
            list_item.setText(val)
            self.lstUniqueValues.addItem(list_item)

        # Populate assigned values tree
        self.treeClasses.clear()
        bold_font = QtGui.QFont()
        bold_font.setItalic(True)
        bold_font.setBold(True)
        bold_font.setWeight(75)
        self.treeClasses.invisibleRootItem().setFlags(QtCore.Qt.ItemIsEnabled)
        for cls in default_classes:
            # Create branch for class
            tree_branch = QtGui.QTreeWidgetItem(self.treeClasses)
            tree_branch.setFlags(QtCore.Qt.ItemIsDropEnabled |
                                 QtCore.Qt.ItemIsEnabled)
            tree_branch.setExpanded(True)
            tree_branch.setFont(0, bold_font)
            tree_branch.setText(0, cls['name'])
            # Assign known values
            for val in assigned_values[cls['name']]:
                tree_leaf = QtGui.QTreeWidgetItem(tree_branch)
                tree_leaf.setFlags(QtCore.Qt.ItemIsEnabled |
                                   QtCore.Qt.ItemIsSelectable |
                                   QtCore.Qt.ItemIsDragEnabled)
                tree_leaf.setText(0, val)

    def go_to_step(self, step):
        """Set the stacked widget to the given step

        :param step: The step number to be moved to
        :type step: int
        """
        self.stackedWidget.setCurrentIndex(step-1)
        self.lblStep.setText(self.tr('step %d') % step)
        self.pbnBack.setEnabled(step > 1)

    # prevents actions being handled twice
    @pyqtSignature('')
    def on_pbnNext_released(self):
        """Automatic slot executed when the pbnNext button is released."""
        current_step = self.stackedWidget.currentIndex() + 1
        # Determine the new step to be switched
        new_step = self.compute_next_step(current_step)

        # Prepare the next tab
        if new_step == step_subcategory:
            self.update_subcategory_tab()
        elif new_step == step_unit:
            self.update_unit_tab()
        elif new_step == step_field:
            self.update_field_tab()
        elif new_step == step_classify:
            self.update_classify_tab()
        elif new_step is None:
            # Complete
            self.accept()
            return

        # Set Next button label
        if new_step == self.stackedWidget.count():
            self.pbnNext.setText(self.tr('Finish'))
        # Disable the Next button unless new data already entered
        self.pbnNext.setEnabled(self.is_ready_to_next_step(new_step))
        self.go_to_step(new_step)

    # prevents actions being handled twice
    @pyqtSignature('')
    def on_pbnBack_released(self):
        """Automatic slot executed when the pbnBack button is released."""
        current_step = self.stackedWidget.currentIndex() + 1
        new_step = self.compute_previous_step(current_step)
        # Set Next button label
        self.pbnNext.setText(self.tr('Next'))
        self.pbnNext.setEnabled(True)
        self.go_to_step(new_step)

    def is_ready_to_next_step(self, step):
        """Check if widgets are filled an new step can be enabled

        :param step: The present step number
        :type step: int

        :returns: True if new step may be enabled
        :rtype: bool
        """
        if step == step_category:
            return bool(self.selected_category())
        if step == step_subcategory:
            return bool(self.selected_subcategory())
        if step == step_unit:
            return bool(self.selected_unit())
        if step == step_field:
            return bool(self.selected_field() or not self.lstFields.count())
        if step == step_classify:
            # Allow to not classify any values
            return True
        if step == step_source:
            # The source_* keywords are not required
            return True
        if step == step_title:
            return bool(self.leTitle.text())

    def compute_next_step(self, current_step):
        """Determine the next step to be switched to

        :param current_step: The present step number
        :type current_step: int

        :returns: The next step number or None if finished
        :rtype: int
        """
        if current_step == step_category:
            category = self.selected_category()
            if self.kw_api.subcategories_for_layer(
                    self.layer_type, self.data_type, category):
                new_step = step_subcategory
            else:
                new_step = step_field
        elif current_step == step_subcategory:
            subcategory = self.selected_subcategory()
            if self.kw_api.units_for_layer(
                    self.layer_type, self.data_type, subcategory):
                new_step = step_unit
            else:
                new_step = step_field
        elif current_step == step_field:
            subcategory = self.selected_subcategory()
            unit_details = self.selected_unit_details()
            if unit_details and unit_details['constraint'] == 'categorical':
                new_step = step_classify
            else:
                new_step = step_source
        elif current_step in (step_unit, step_classify, step_source):
            new_step = current_step + 1
        elif current_step == step_title:
            new_step = None
        else:
            raise Exception('Unexpected number of steps')

        # Skip the field (and classify) tab if raster layer
        if new_step == step_field and is_raster_layer(self.layer):
            new_step = step_source

        return new_step

    def compute_previous_step(self, current_step):
        """Determine the previous step to be switched to (by the Back button)

        :param current_step: The present step number
        :type current_step: int

        :returns: The previous step number
        :rtype: int
        """
        if current_step == step_source:
            if self.selected_mapping():
                new_step = step_classify
            elif self.selected_field():
                new_step = step_field
            elif self.selected_unit():
                new_step = step_unit
            elif self.selected_subcategory():
                new_step = step_subcategory
            else:
                new_step = step_category
        elif current_step == step_field:
            if self.selected_unit():
                new_step = step_unit
            elif self.selected_subcategory():
                new_step = step_subcategory
            else:
                new_step = step_category
        else:
            new_step = current_step - 1
        return new_step

    def get_keywords(self):
        """Obtain the state of the dialog as a keywords dict.

        :returns: Keywords reflecting the state of the dialog.
        :rtype: dict
        """
        my_keywords = {}
        if self.selected_category():
            my_keywords['category'] = self.selected_category()
        if self.selected_subcategory():
            my_keywords['subcategory'] = self.selected_subcategory()
        if self.selected_unit():
            my_keywords['unit'] = self.selected_unit()
        if self.lstFields.currentItem():
            my_keywords['field'] = self.lstFields.currentItem().text()
        if self.leSource.text():
            my_keywords['source'] = self.leSource.text()
        if self.leSource_url.text():
            my_keywords['source_url'] = self.leSource_url.text()
        if self.leSource_scale.text():
            my_keywords['source_scale'] = self.leSource_scale.text()
        if self.leSource_date.text():
            my_keywords['source_date'] = self.leSource_date.text()
        if self.leTitle.text():
            my_keywords['title'] = self.leTitle.text()
        value_map = self.selected_mapping()
        if value_map:
            my_keywords['value_map'] = str(value_map)
        return my_keywords

    def accept(self):
        """Automatic slot executed when the Finish button is pressed.

        It will write out the keywords for the layer that is active.
        This method is based on the KeywordsDialog class.
        """
        self.keyword_io = KeywordIO()
        my_keywords = self.get_keywords()
        try:
            self.keyword_io.write_keywords(
                layer=self.layer, keywords=my_keywords)
        except InaSAFEError, e:
            myErrorMessage = get_error_message(e)
            # noinspection PyCallByClass,PyTypeChecker,PyArgumentList
            QtGui.QMessageBox.warning(
                self, self.tr('InaSAFE'),
                ((self.tr(
                    'An error was encountered when saving the keywords:\n'
                    '%s') % myErrorMessage.to_html())))
        if self.dock is not None:
            self.dock.get_layers()
        self.done(QtGui.QDialog.Accepted)
