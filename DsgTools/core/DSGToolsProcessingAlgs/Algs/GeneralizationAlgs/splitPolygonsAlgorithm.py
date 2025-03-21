# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2023-04-15
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Felipe Diniz - Cartographic Engineer @ Brazilian Army
        email                : diniz.felipe@eb.mil.br
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import math
from itertools import product

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsFeatureSink,
    QgsField,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsRectangle,
    QgsSpatialIndex,
    QgsVectorLayer,
)


class SplitPolygons(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    PARAM = "PARAM"
    OVERLAP = "OVERLAP"
    OUTPUT = "OUTPUT"
    SPLIT_FACTORS = ["1/1", "1/4", "1/9", "1/16", "1/25"]

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT, "Input polygon layer", [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.PARAM,
                "Splitting factor",
                options=self.SPLIT_FACTORS,
                defaultValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.OVERLAP,
                "Overlap value",
                QgsProcessingParameterNumber.Double,
                defaultValue=0.002,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT, "Output split polygons")
        )

    def splitPol(
        self,
        features,
        overlap,
        fields,
        side_length,
        col_steps,
        row_steps,
        idToFeature,
        index,
        feedback,
    ):
        polygons = []
        for feature in features:
            if feedback.isCanceled():
                break

            geometry = feature.geometry()
            source_fid = feature.id()

            xmin, ymin, xmax, ymax = geometry.boundingBox().toRectF().getCoords()
            width = xmax - xmin
            height = ymax - ymin

            for i, j in product(range(col_steps), range(row_steps)):
                if feedback.isCanceled():
                    break
                x1 = xmin + (width * i * side_length)
                y1 = ymin + (height * j * side_length)
                x2 = xmin + (width * (i + 1) * side_length)
                y2 = ymin + (height * (j + 1) * side_length)

                new_geom = QgsGeometry.fromRect(QgsRectangle(x1, y1, x2, y2))

                # Buffer the new geometry
                buffered_geom = new_geom.buffer(
                    overlap, 5
                )  # 5 is the default number of segments per quarter circle

                # Use the spatial index to find intersecting features
                candidate_ids = index.intersects(buffered_geom.boundingBox())
                if not candidate_ids:
                    continue

                # Dissolve only intersecting features
                dissolved_geometry = QgsGeometry.unaryUnion(
                    [idToFeature[cid].geometry() for cid in candidate_ids]
                )

                # Clip the buffered geometry by the dissolved geometry
                intersected_geom = buffered_geom.intersection(dissolved_geometry)

                if intersected_geom.isEmpty():
                    continue

                new_feature = QgsFeature(feature)
                new_feature.setGeometry(intersected_geom)
                new_feature.setFields(fields)
                polygons.append(new_feature)
        return polygons

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        split_factor = self.parameterAsEnum(parameters, self.PARAM, context)
        overlap = self.parameterAsDouble(parameters, self.OVERLAP, context)

        # Add a new field called "priority" to the output layer's fields
        fields = source.fields()
        fields.append(QgsField("priority", QVariant.Int))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            source.wkbType(),
            source.sourceCrs(),
        )

        features = list(source.getFeatures())
        idToFeature = {}
        for feat in features:
            idToFeature[feat.id()] = feat

        # Create a spatial index
        index = QgsSpatialIndex(source)

        parts = [1, 4, 9, 16, 25][split_factor]
        side_length = math.sqrt(1 / parts)
        col_steps = int(math.sqrt(parts))
        row_steps = col_steps

        polygons = self.splitPol(
            features,
            overlap,
            fields,
            side_length,
            col_steps,
            row_steps,
            idToFeature,
            index,
            feedback,
        )
        base_polygons = self.splitPol(
            features, overlap, fields, 1, 1, 1, idToFeature, index, feedback
        )

        tile_layer = QgsVectorLayer(
            "Polygon?crs=" + source.sourceCrs().authid(), "tile_polygons", "memory"
        )
        tile_data_provider = tile_layer.dataProvider()
        tile_data_provider.addAttributes(fields)
        tile_layer.updateFields()
        tile_data_provider.addFeatures(polygons)
        tile_layer.updateExtents()
        index_tile = QgsSpatialIndex(tile_layer)
        idToFeatureTile = {}
        for feat in tile_layer.getFeatures():
            idToFeatureTile[feat.id()] = feat

        base_layer = QgsVectorLayer(
            "Polygon?crs=" + source.sourceCrs().authid(), "base_polygons", "memory"
        )
        base_data_provider = base_layer.dataProvider()
        base_data_provider.addAttributes(fields)
        base_layer.updateFields()
        base_data_provider.addFeatures(base_polygons)
        base_layer.updateExtents()
        index_base = QgsSpatialIndex(base_layer)
        idToFeatureBase = {}
        for feat in base_layer.getFeatures():
            idToFeatureBase[feat.id()] = feat

        priority = 1
        final_features = {}
        base_used = []

        sorted_source_features = sorted(
            source.getFeatures(),
            key=lambda x: (
                round(x.geometry().centroid().asPoint().y(), 5),
                -round(x.geometry().centroid().asPoint().x(), 5),
            ),
            reverse=True,
        )
        for feat in sorted_source_features:
            # Use the spatial index to find intersecting features
            geometry = feat.geometry()
            candidate_ids = index_base.intersects(geometry.boundingBox())
            intersecting_features_base = [idToFeatureBase[cid] for cid in candidate_ids]
            intersecting_features_base.sort(
                key=lambda x: (
                    round(x.geometry().centroid().asPoint().y(), 5),
                    -round(x.geometry().centroid().asPoint().x(), 5),
                )
                if not x.geometry().isNull()
                else (0, 0),
                reverse=True,
            )
            for base_polygon in intersecting_features_base:
                if base_polygon.id() in base_used:
                    continue
                base_used.append(base_polygon.id())

                base_geometry = base_polygon.geometry()
                candidate_ids = index_tile.intersects(base_geometry.boundingBox())
                intersecting_features = [idToFeatureTile[cid] for cid in candidate_ids]

                intersecting_features.sort(
                    key=lambda x: (
                        round(x.geometry().centroid().asPoint().y(), 5),
                        -round(x.geometry().centroid().asPoint().x(), 5),
                    )
                    if not x.geometry().isNull()
                    else (0, 0),
                    reverse=True,
                )
                for polygon in intersecting_features:
                    if polygon.id() in final_features:
                        continue
                    polygon.setAttribute("priority", priority)
                    final_features[polygon.id()] = polygon
                    priority += 1

        for polygon in final_features.values():
            sink.addFeature(polygon, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}

    def name(self):
        return "splitpolygons"

    def displayName(self):
        return "Split Polygons"

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr("Generalization Algorithms")

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "DSGTools - Generalization Algorithms"

    def tr(self, string):
        return QCoreApplication.translate("SplitPolygons", string)

    def createInstance(self):
        return SplitPolygons()
