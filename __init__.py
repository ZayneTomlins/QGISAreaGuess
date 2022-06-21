#-----------------------------------------------------------
# Copyright (C) 2015 Martin Dobias
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------
import random

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QAction
from qgis._core import QgsProject, QgsMessageOutput
from qgis._gui import QgsMapToolEmitPoint, QgsVertexMarker
from qgis.core import QgsFeatureRequest, QgsRectangle, QgsDistanceArea, QgsPointXY
from qgis.utils import iface


def classFactory(iface):
    return MinimalPlugin(iface)


class MinimalPlugin:
    def __init__(self, iface):
        self.point = None
        self.iface = iface

    def initGui(self):
        self.point_list = []
        self.action = QAction("New Game", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def lose(self):
        activeLayer = iface.activeLayer()
        request = QgsFeatureRequest()
        rect = QgsRectangle(self.point[0].x(), self.point[0].y(), self.point[0].x(), self.point[0].y())
        request.setFilterRect(rect)
        features = list(activeLayer.getFeatures(request))
        print(f"You lose! The country was {features[0]['NAME']}")

    def on_clicked(self, point, button):
        self.loc = point

        request = QgsFeatureRequest()
        rect = QgsRectangle(point.x(), point.y(), point.x(), point.y())
        request.setFilterRect(rect)
        activeLayer = iface.activeLayer()
        features = list(activeLayer.getFeatures(request))
        #print(features)
        try:
            if features[0].id() == self.country and len(features) == 1 and self.clicks_left > 0:
                print(f"You win! The country was {features[0]['NAME']}")
            elif (len(features) > 1):
                print("You can only click on one country at a time")
            else:
                self.clicks_left -= 1
                self.generate_dot(point)
                if (self.clicks_left <= 0):
                    self.lose()
                else:
                    self.getOrientation(point)
        except IndexError:
            print("You must click on a country")

    def on_selection_changed(self, selected, deselected, clear):
        print(selected)

    def getOrientation(self, point):
        x1 = point.x()
        y1 = point.y()
        x2 = self.point[0].x()
        y2 = self.point[0].y()

        p1 = QgsPointXY(x1, y1)
        p2 = QgsPointXY(x2, y2)
        xdir = None
        ydir = None

        if (x1 > x2):
            xdir = "West"
        elif (x1 < x2):
            xdir = "East"
        if (y1 > y2):
            ydir = "South"
        elif (y1 < y2):
            ydir = "North"

        distobj = QgsDistanceArea()
        distobj.setSourceCrs(iface.mapCanvas().mapSettings().destinationCrs(), QgsProject.instance().transformContext())
        distobj.setEllipsoid(QgsProject.instance().ellipsoid())
        dist = distobj.measureLine(p1, p2)
        dist /= 100000
        dist = int(dist)
        print(f"The country is {xdir}, {ydir}, about {dist * 100}km away")
        #self.message.setMessage(f"The country is {xdir}, {ydir}, about {dist * 100}×10^3km away")
        if (self.clicks_left > 0):
            print(f"You have {self.clicks_left} clicks left")
        return

    def generate_dot(self, points):
        activeLayer = iface.activeLayer()
        canvas = iface.mapCanvas()
        canvas.setExtent(activeLayer.extent())
        v = QgsVertexMarker(canvas)
        v.setCenter(QgsPointXY(points.x(), points.y()))
        v.setColor(QColor(255, 10, 10))
        v.setIconSize(5)
        v.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        v.setPenWidth(3)
        self.point_list.append(v)

    def run(self):
        self.feature_ids = []
        self.clicks_left = 6
        #self.message = self.createMessageOutput()
        canvas = iface.mapCanvas()
        for point in self.point_list:
            canvas.scene().removeItem(point)
        size = canvas.fullExtent()

        self.map_tool = QgsMapToolEmitPoint(canvas)
        if self.clicks_left > 0:
            self.map_tool.canvasClicked.connect(self.on_clicked)

        iface.mapCanvas().setMapTool(self.map_tool)

        activeLayer = iface.activeLayer()
        activeLayer.selectionChanged.connect(self.on_selection_changed)
        features = list(activeLayer.getFeatures())

        for feature in features:
            # retrieve every feature with its geometry and attributes
            self.feature_ids.append(feature.id())
            #print(feature.id())

        self.country = self.feature_ids[random.randint(0, len(self.feature_ids))]
        #print(self.country)

        for feature in features:
            # retrieve every feature with its geometry and attributes
            if (self.country == feature.id()):
                generated = False
                while (generated == False):
                    try:
                        feature = activeLayer.getGeometry(self.country)
                        seed = random.randint(0, 24)
                        self.point = feature.randomPointsInPolygon(1, seed)
                        generated = True
                    except ValueError:
                        generated = False


        """
        canvas = iface.mapCanvas()
        canvas.setExtent(activeLayer.extent())
        v = QgsVertexMarker(canvas)
        v.setCenter(QgsPointXY(points[0].x(), points[0].y()))
        v.setColor(QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        v.setIconSize(5)
        v.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        v.setPenWidth(3)

        self.point_list.append(v)
        """


        """
        for selected in selection:
            # retrieve every feature with its geometry and attributes
            print("Feature ID: ", selected.id())
            # fetch geometry
            # show some information about the feature geometry
            geom = selected.geometry()
            geomSingleType = QgsWkbTypes.isSingleType(geom.wkbType())
            if geom.type() == QgsWkbTypes.PointGeometry:
                # the geometry type can be of single or multi type
                if geomSingleType:
                    x = geom.asPoint()
                    print("Point: ", x)
                else:
                    x = geom.asMultiPoint()
                    print("MultiPoint: ", x)
            elif geom.type() == QgsWkbTypes.LineGeometry:
                if geomSingleType:
                    x = geom.asPolyline()
                    print("Line: ", x, "length: ", geom.length())
                else:
                    x = geom.asMultiPolyline()
                    print("MultiLine: ", x, "length: ", geom.length())
            elif geom.type() == QgsWkbTypes.PolygonGeometry:
                if geomSingleType:
                    x = geom.asPolygon()
                    print("Polygon: ", x, "Area: ", geom.area())
                else:
                    x = geom.asMultiPolygon()
                    print("MultiPolygon: ", x, "Area: ", geom.area())
            else:
                print("Unknown or invalid geometry")
            # fetch attributes
            attrs = selected.attributes()
            # attrs is a list. It contains all the attribute values of this feature
            print(attrs)
        """


"""
        for feature in features:
            # retrieve every feature with its geometry and attributes
            print("Feature ID: ", feature.id())
            # fetch geometry
            # show some information about the feature geometry
            geom = feature.geometry()
            geomSingleType = QgsWkbTypes.isSingleType(geom.wkbType())
            if geom.type() == QgsWkbTypes.PointGeometry:
                # the geometry type can be of single or multi type
                if geomSingleType:
                    x = geom.asPoint()
                    print("Point: ", x)
                else:
                    x = geom.asMultiPoint()
                    print("MultiPoint: ", x)
            elif geom.type() == QgsWkbTypes.LineGeometry:
                if geomSingleType:
                    x = geom.asPolyline()
                    print("Line: ", x, "length: ", geom.length())
                else:
                    x = geom.asMultiPolyline()
                    print("MultiLine: ", x, "length: ", geom.length())
            elif geom.type() == QgsWkbTypes.PolygonGeometry:
                if geomSingleType:
                    x = geom.asPolygon()
                    print("Polygon: ", x, "Area: ", geom.area())
                else:
                    x = geom.asMultiPolygon()
                    print("MultiPolygon: ", x, "Area: ", geom.area())
            else:
                print("Unknown or invalid geometry")
            # fetch attributes
            attrs = feature.attributes()
            # attrs is a list. It contains all the attribute values of this feature
            print(attrs)
"""