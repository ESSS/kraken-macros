from __future__ import unicode_literals

'''
Created on 5 de out de 2015

@author: viniciusgs
'''
from kraken20.plugins.curve_calculation.semantic_association_crossed_curve_with_source import SemanticAssociationCrossedCurveWithSource
from kraken20.plugins.curve_calculation.curve_calculation import ICurveCalculation
from esss_qt10.qt_traits.process_events import ProcessEvents
from petroapp10.plugins.entities._entities import GetSubjects
from plugins10core.pluginmanager import PluginManager
from petroapp10.plugins.colorings_control.colorings_control_plugins import EPColoringControl

class CrossApiUtils(object):


    def ClearCrossedCurvesFromModel(self, model):
        '''
        Deletes all crossed curves from the given model. Any requested crossed curve will be fully recalculated
        '''
        try:
            curve_calculation = model.subject.GetAdapter(ICurveCalculation)
            curve_calculation._cross_curve_calculation._curves_cache.clear()
        except:
            # It was not possible to remove the curve, should we break it?
            # raise
            pass

    def _GetColoring(self, ka_model, ka_window):
        import time

        window_subject = ka_window.subject
        for _i in xrange(5):

            coloring_control = PluginManager.GetSingleton(EPColoringControl)
            colorings = coloring_control.GetCurrentColorings('visible', ka_model.subject.id, window_subject.id)

            if len(colorings) == 1:
                return colorings.pop()

            time.sleep(1)
            ProcessEvents()

        raise RuntimeError('No Coloring found for: %s' %ka_model.GetName())


    def CreateCrossCurve(self, ka_model, image_name, domain_name, ka_window):

        '''
        Generates a crossed curve based on the given curve names, and display that curve in the given window. Use it
        if you think that this is better then the current macro handling
        '''
        # Obtaining image semantic association
        image_curve = ka_model.GetCurve(image_name)
        image_association = image_curve._curve_info.GetInfo().curve_association

        # Obtaining domain semantic association
        domain_curve = ka_model.GetCurve(domain_name)
        domain_association = domain_curve._curve_info.GetInfo().curve_association

        # Creating a semantic association that represents the crossed curve
        cross_association = SemanticAssociationCrossedCurveWithSource(
            domain_association, image_association, SemanticAssociationCrossedCurveWithSource.CROSSED_CURVE_CURVE_SOURCE)

        coloring_process = self._GetColoring(ka_model, ka_window)

        # Adding the crossed curves to the curves currently visible
        current_curves =  coloring_process.curve_associations[:]
        current_curves.append(cross_association)
        coloring_process.curve_associations = current_curves

        ka_window.subject.gui.ForceModifiedAndRequestUpdate()
        ProcessEvents()


