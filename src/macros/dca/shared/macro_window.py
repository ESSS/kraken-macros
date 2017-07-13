'''
Warning: Changes in this file may not be correctly interpreted later on in the macro engine.

Generated script file.

Name for generated for macro: Workspace Window2

Commands Description for Macro:
Open Export Dialog for: Main Grid

'''
from plugins10.plugins.uiapplication.model_eps import EPModel
from plugins10.plugins.workspace.workspace_editor_subjects.workspace_editor_subjects import (
    WorkspaceEditorSubject)
from petroapp10.plugins.entities.plot_window_subject.plot_window_subject_model import (
    PlotWindowSubject as BaseWindowSubject)
from plugins10.plugins.mainwindow.mainwindowplugins.centralwidget import DefaultCentralEditor
from plots10.plot.plot import Plot


class BrentPlotWindow(Plot, DefaultCentralEditor):
     
     
    def __init__(self, parent, central_editor_id, *args, **kwargs):
        DefaultCentralEditor.__init__(self, central_editor_id)
        Plot.__init__(self, parent)
        

#===================================================================================================
# BrentPlotWindowSubject
#===================================================================================================
class BrentPlotWindowSubject(WorkspaceEditorSubject):

    def GetGUIClass(self):
        '''
        @see: BaseTimeDependentPlotWindowSubject.GetGUIClass
        '''
        return BrentPlotWindow


pool = PluginManager.GetSingleton(EPModel)

subject = BrentPlotWindowSubject()
for i in xrange(10):
    sid = 'muwindow%d' % i
    if sid not in pool:
        pool[sid] = subject
        break

print subject.gui
print subject.gui.show()