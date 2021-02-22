# -*- coding: utf-8 -*-

from Plugins.Plugin import PluginDescriptor
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from XMLConfigTools import ERROR_LEVEL, WARN_LEVEL, DEBUG_LEVEL, getGeneralLogger
from traceback import format_exc

from . import _

XMLConfigHelpfile = None
XMLConfigMainHelp = None
try:
	from Plugins.SystemPlugins.MPHelp import registerHelp, XMLHelpReader
	
	XMLConfigHelpfile = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/xmlConfigTool") + "/mphelp.xml"
	reader = XMLHelpReader(XMLConfigHelpfile)
	XMLConfigMainHelp = registerHelp(*reader)
except:
	getGeneralLogger().printOut("Help-Init-Error:\n%s" % str(format_exc()), level = ERROR_LEVEL)

def showMainHelp(session, **kwargs):
	try:
		if XMLConfigMainHelp:
			XMLConfigMainHelp.open(session)
	except:
		getGeneralLogger().printOut("showMainHelp-Error:\n%s" % str(format_exc()), level = ERROR_LEVEL)

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name = _("XML-Config-Tool"),
			description = _("General XML-Config-Support"),
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = showMainHelp)
	]