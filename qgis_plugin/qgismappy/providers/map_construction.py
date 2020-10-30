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
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterDistance, QgsWkbTypes, QgsFeatureSink,
                       QgsProcessingParameterField)


class MapConstructionProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    IN_LINES = 'IN_LINES'
    IN_POINTS = 'IN_POINTS'
    EXT_DISTANCE = "EXT_DISTANCE"
    OUTPUT = 'OUTPUT'
    # MAIN_FIELD = "MAIN_FIELD"

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return MapConstructionProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'myscript'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Map Construction')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Mapping')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'mapping'



    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Generate consistent polygonal layers starting from limits and indicator points. This tool execute in sequences the following operations for you:\n"
                       "- removes null geometries\n"
                       "- remove duplicated vertices\n"
                       "- extend lines to grant intersection\n"
                       "- polygonize the lines\n"
                       "- assign fileds to polygons using the points layer (via a spatial join)\n"
                       "The output is a polygonal layer with granted topological consistency (no overalps, holes, duplicated geometries etc), perfect for a geological map.")



    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.IN_LINES,
                self.tr('Input Lines'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.IN_POINTS,
                self.tr('Input Points'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterDistance(self.EXT_DISTANCE, self.tr('Extend Lines Distance'), defaultValue=0.0,
                                           minValue=0.0, optional=True, parentParameterName=self.IN_LINES))

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        # self.addParameter(
        #     QgsProcessingParameterFeatureSink(
        #         self.OUTPUT,
        #         self.tr('Constructed Map')
        #     )
        # )

        # self.addParameter(QgsProcessingParameterField(self.MAIN_FIELD, self.tr("Main Field (mostly for rendering)"),
        #                                               parentLayerParameterName=self.IN_POINTS))

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Constructed Map')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source_lines and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source_lines = self.parameterAsSource(
            parameters,
            self.IN_LINES,
            context
        )

        source_pts = self.parameterAsSource(
            parameters,
            self.IN_POINTS,
            context
        )

        # field = self.parameterAsString(parameters, self.MAIN_FIELD, context)
        distance = self.parameterAsDouble(parameters, self.EXT_DISTANCE, context)

        # If source_lines was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source_lines cannot be evaluated
        if source_lines is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.IN_LINES))

        if source_pts is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.IN_POINTS))

        # Send some information to the user
        feedback.pushInfo('CRS is {}'.format(source_lines.sourceCrs().authid()))

        # Compute the number of steps to display within the progress bar and
        # get features from source_lines
        # total = 100.0 / source_lines.featureCount() if source_lines.featureCount() else 0
        # features = source_lines.getFeatures()
        #
        # for current, feature in enumerate(features):
        #     # Stop the algorithm if cancel button has been clicked
        #     if feedback.isCanceled():
        #         break
        #
        #     # Add a feature in the sink
        #     sink.addFeature(feature, QgsFeatureSink.FastInsert)
        #
        #     # Update the progress bar
        #     feedback.setProgress(int(current * total))

        # To run another Processing algorithm as part of this algorithm, you can use
        # processing.run(...). Make sure you pass the current context and feedback
        # to processing.run to ensure that all temporary layer outputs are available
        # to the executed algorithm, and that the executed algorithm can send feedback
        # reports to the user (and correctly handle cancellation and progress reports!)

        if feedback.isCanceled():
            return {}

        nonnull = processing.run("native:removenullgeometries",
                                 {'INPUT': parameters[self.IN_LINES],
                                  'OUTPUT': 'memory:', 'REMOVE_EMPTY': True}, context=context,
                                 feedback=feedback, is_child_algorithm=True)

        nodups = processing.run("native:removeduplicatevertices",
                                {'INPUT': nonnull["OUTPUT"],
                                 'OUTPUT': 'memory:', "TOLERANCE": 1e-06,
                                 'USE_Z_VALUE=': False}, context=context,
                                feedback=feedback, is_child_algorithm=True)

        extended_layer = processing.run("native:extendlines",
                                        {'END_DISTANCE': distance,
                                         'INPUT': nodups["OUTPUT"],
                                         'OUTPUT': 'memory:', 'START_DISTANCE': distance}, context=context,
                                        feedback=feedback, is_child_algorithm=True)

        polygonized_layer = processing.run("native:polygonize", {
            'INPUT': extended_layer["OUTPUT"],
            'OUTPUT': 'memory:',
        }, context=context, feedback=feedback, is_child_algorithm=True)

        joined_layer = processing.run("native:joinattributesbylocation",
                                      {'DISCARD_NONMATCHING': False,
                                       'INPUT': polygonized_layer["OUTPUT"],
                                       'JOIN': parameters[self.IN_POINTS],
                                       'JOIN_FIELDS': [],
                                       'METHOD': 1,
                                       'OUTPUT': "memory:",
                                       'PREDICATE': [0],
                                       'PREFIX': ''}

                                      , context=context, feedback=feedback, is_child_algorithm=False)
        feedback.pushInfo(f"layer is {joined_layer}")

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            joined_layer["OUTPUT"].fields(),  # QgsFields() for an empty fields list or source_lines.fields()
            QgsWkbTypes.Polygon,
            source_lines.sourceCrs()
        )

        feedback.pushInfo(f"destination {dest_id}")
        #
        # # If sink was not created, throw an exception to indicate that the algorithm
        # # encountered a fatal error. The exception text can be any string, but in this
        # # case we use the pre-built invalidSinkError method to return a standard
        # # helper text for when a sink cannot be evaluated
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        #
        for feature in joined_layer["OUTPUT"].getFeatures():
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

        # from qgismappy.qgismappy_dockwidget import resetCategoriesIfNeeded
        # resetCategoriesIfNeeded(sink, field)

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT: dest_id}
