from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider

from .map_construction import MapConstructionProcessingAlgorithm
from .map_autostyle import MapAutoStyleProcessingAlgorithm


class Provider(QgsProcessingProvider):


    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(MapConstructionProcessingAlgorithm())
        self.addAlgorithm(MapAutoStyleProcessingAlgorithm())
        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self, *args, **kwargs):
        """The ID of your plugin, used for identifying the provider.

        This string should be a unique, short, character only string,
        eg "qgis" or "gdal". This string should not be localised.
        """
        return 'mappy'

    def name(self, *args, **kwargs):
        """The human friendly name of your plugin in Processing.

        This string should be as short as possible (e.g. "Lastools", not
        "Lastools version 1.0.1 64-bit") and localised.
        """
        return self.tr('Mappy')

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QIcon(':/plugins/qgismappy/icon.png')