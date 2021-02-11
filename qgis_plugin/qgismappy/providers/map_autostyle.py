# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication
from qgis._core import Qgis, QgsProcessingParameterBoolean, QgsProcessingUtils
from qgis.gui import QgsMessageBar
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterDistance, QgsWkbTypes, QgsFeatureSink,
                       QgsProcessingParameterField)


from qgis.utils import iface

from qgis.PyQt.QtGui import QIcon

from ..qgismappy_dockwidget import resetCategoriesIfNeeded

class MapAutoStyleProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    Helper to assign categorized style to a polygonal layer
    """

    def icon(self):
        return QIcon(':/plugins/qgismappy/mapstyle.png')


    IN_POLYGONS = "IN_POLYGONS"
    CAT_FIELD = "CAT_FIELD"
    STYLE_UNASSIGNED = "STYLE_UNASSIGNED"

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return MapAutoStyleProcessingAlgorithm()

    def name(self):
        return 'mapautostyle'

    def displayName(self):
        return self.tr('Map Automatic Styling')

    def group(self):
        return self.tr('Style')

    def groupId(self):
        return 'style'



    def shortHelpString(self):
        return self.tr("""Generate or update styling for a polygon layer created by mappy's map generation tool""")


    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.IN_POLYGONS,
                self.tr('Input Lines'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.CAT_FIELD,
                self.tr('Units field in point layer'),
                parentLayerParameterName = self.IN_POLYGONS,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.STYLE_UNASSIGNED,
                self.tr('Create category also for unassigned polygons'),
                defaultValue=True, optional=False
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        polygons_layer = self.parameterAsLayer(
            parameters,
            self.IN_POLYGONS,
            context
        )

        fieldname = self.parameterAsString(parameters, self.CAT_FIELD, context)
        unassigned = self.parameterAsBool(parameters, self.STYLE_UNASSIGNED, context)
        feedback.pushInfo(f"field used is {fieldname}")

        from ..qgismappy_dockwidget import resetCategoriesIfNeeded
        resetCategoriesIfNeeded(polygons_layer, fieldname, unassigned=unassigned)
        return {}

