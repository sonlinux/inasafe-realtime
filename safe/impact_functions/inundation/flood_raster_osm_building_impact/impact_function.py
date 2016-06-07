# coding=utf-8
"""InaSAFE Disaster risk tool by Australian Aid - Flood Raster Impact on OSM
Buildings

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'lucernae'

import logging

from safe.impact_functions.inundation\
    .flood_raster_osm_building_impact.metadata_definitions import \
    FloodRasterBuildingMetadata
from safe.impact_functions.bases.continuous_rh_classified_ve import \
    ContinuousRHClassifiedVE
from safe.storage.vector import Vector
from safe.utilities.i18n import tr
from safe.common.utilities import verify
from safe.utilities.utilities import main_type
from safe.engine.interpolation import assign_hazard_values_to_exposure_data
from safe.impact_reports.building_exposure_report_mixin import (
    BuildingExposureReportMixin)
LOGGER = logging.getLogger('InaSAFE')


class FloodRasterBuildingFunction(
        ContinuousRHClassifiedVE,
        BuildingExposureReportMixin):
    # noinspection PyUnresolvedReferences
    """Inundation raster impact on building data."""
    _metadata = FloodRasterBuildingMetadata()

    def __init__(self):
        """Constructor (calls ctor of base class)."""
        super(FloodRasterBuildingFunction, self).__init__()

        # From BuildingExposureReportMixin
        self.building_report_threshold = 25

    def notes(self):
        """Return the notes section of the report as dict.

        :return: The notes that should be attached to this impact report.
        :rtype: dict
        """
        title = tr('Notes and assumptions')
        threshold = self.parameters['threshold'].value
        fields = [
            tr('Buildings are flooded when flood levels exceed %.1f m')
            % threshold,
            tr('Buildings are wet when flood levels are greater than 0 m but '
               'less than %.1f m') % threshold,
            tr('Buildings are dry when flood levels are 0 m.'),
            tr('Buildings are closed if they are flooded or wet.'),
            tr('Buildings are open if they are dry.')
        ]

        return {
            'title': title,
            'fields': fields
        }

    @property
    def _affected_categories(self):
        """Overwriting the affected categories, since 'unaffected' are counted.

        :returns: The categories that equal affected.
        :rtype: list
        """
        return [tr('Flooded'), tr('Wet')]

    def run(self):
        """Flood impact to buildings (e.g. from Open Street Map)."""

        threshold = self.parameters['threshold'].value  # Flood threshold [m]

        verify(isinstance(threshold, float),
               'Expected thresholds to be a float. Got %s' % str(threshold))

        # Determine attribute name for hazard levels
        hazard_attribute = 'depth'

        # Interpolate hazard level to building locations
        interpolated_layer = assign_hazard_values_to_exposure_data(
            self.hazard.layer,
            self.exposure.layer,
            attribute_name=hazard_attribute)

        # Extract relevant exposure data
        features = interpolated_layer.get_data()
        total_features = len(interpolated_layer)

        structure_class_field = self.exposure.keyword('structure_class_field')
        exposure_value_mapping = self.exposure.keyword('value_mapping')

        hazard_classes = [tr('Flooded'), tr('Wet'), tr('Dry')]
        self.init_report_var(hazard_classes)

        for i in range(total_features):
            # Get the interpolated depth
            water_depth = float(features[i]['depth'])
            if water_depth <= 0:
                inundated_status = 0  # dry
            elif water_depth >= threshold:
                inundated_status = 1  # inundated
            else:
                inundated_status = 2  # wet

            usage = features[i].get(structure_class_field, None)
            usage = main_type(usage, exposure_value_mapping)

            # Add calculated impact to existing attributes
            features[i][self.target_field] = inundated_status
            category = [
                tr('Dry'),
                tr('Flooded'),
                tr('Wet')][inundated_status]
            self.classify_feature(category, usage, True)

        self.reorder_dictionaries()

        # Lump small entries and 'unknown' into 'other' category
        # Building threshold #2468
        postprocessors = self.parameters['postprocessors']
        building_postprocessors = postprocessors['BuildingType'][0]
        self.building_report_threshold = building_postprocessors.value[0].value
        self._consolidate_to_other()

        # For printing map purpose
        map_title = tr('Flooded buildings')
        legend_title = tr('Flooded structure status')
        legend_units = tr('(flooded, wet, or dry)')

        style_classes = [
            dict(
                label=tr('Dry (<= 0 m)'),
                value=0,
                colour='#1EFC7C',
                transparency=0,
                size=1
            ),
            dict(
                label=tr('Wet (0 m - %.1f m)') % threshold,
                value=2,
                colour='#FF9900',
                transparency=0,
                size=1
            ),
            dict(
                label=tr('Flooded (>= %.1f m)') % threshold,
                value=1,
                colour='#F31A1C',
                transparency=0,
                size=1
            )]

        style_info = dict(
            target_field=self.target_field,
            style_classes=style_classes,
            style_type='categorizedSymbol')

        impact_data = self.generate_data()

        extra_keywords = {
            'target_field': self.target_field,
            'map_title': map_title,
            'legend_title': legend_title,
            'legend_units': legend_units,
            'buildings_total': total_features,
            'buildings_affected': self.total_affected_buildings
        }

        impact_layer_keywords = self.generate_impact_keywords(extra_keywords)

        impact_layer = Vector(
            data=features,
            projection=interpolated_layer.get_projection(),
            geometry=interpolated_layer.get_geometry(),
            name=tr('Estimated buildings affected'),
            keywords=impact_layer_keywords,
            style_info=style_info)

        impact_layer.impact_data = impact_data
        self._impact = impact_layer
        return impact_layer