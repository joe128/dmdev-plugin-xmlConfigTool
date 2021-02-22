# -*- coding: utf-8 -*-

from . import _

# GUI (Components)
from Components.MenuList import MenuList
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_WRAP
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Sources.StaticText import StaticText
from Tools.BoundFunction import boundFunction
from Components.Pixmap import Pixmap

from skin import parseColor, parseFont

from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.HelpMenu import HelpMenu, HelpableScreen
from Components.ConfigList import ConfigListScreen
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.config import config, configfile, ConfigText, ConfigDirectory, ConfigNumber, KEY_LEFT, KEY_RIGHT, KEY_OK
from Screens.LocationBox import LocationBox
import os

from XMLConfigTools import ERROR_LEVEL, WARN_LEVEL, DEBUG_LEVEL, PLUGIN_VERSION, getGeneralLogger
from traceback import format_exc

"""
class to represent a list of your objects in Overview
"""
class ConfigObjectList(MenuList):
	def __init__(self, entries, loggerInstance = None):
		MenuList.__init__(self, entries, enableWrapAround=True, content=eListboxPythonMultiContent)

		self.l.setFont(0, gFont("Regular", 22))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setItemHeight(25)
		self.colorDisabled = 12368828
		self.log = loggerInstance

	"""
	You have to return a list of the content you want to show in Overview
	"""
	def buildListboxEntry(self, configObject):
		if self.log:
			self.log.printOut("You have to implement \"buildListboxEntry\" to show your objects!", level = ERROR_LEVEL)
		return None

	def applySkin(self, desktop, parent):
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				elif attrib == "colorDisabled":
					self.colorDisabled = parseColor(value).argb()
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return MenuList.applySkin(self, desktop, parent)

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

	def moveToEntry(self, entry):
		if entry is None:
			return

		idx = 0
		for x in self.list:
			if x[0] == entry:
				self.instance.moveSelectionTo(idx)
				break
			idx += 1

"""
	init-params:
		xmlConfigSupportInstance	an instance of XMLConfigSupport
		configObjectListClass		class which manage the Menulist (you can also inherit from ConfigObjectList)
		loggerInstance				instance of GeneralLogger [optional]
	return: boolean if any object was changed
"""
class ConfigObjectOverview(Screen, HelpableScreen):
	CONST_MENU_XMLTOOL_EXPORT = "MENU_XMLTOOL_EXPORT"
	CONST_MENU_XMLTOOL_IMPORT = "MENU_XMLTOOL_IMPORT"
	CONST_MENU_XMLTOOL_HELP = "MENU_XMLTOOL_MAIN_HELP"
	skin = """<screen name="ConfigObjectOverview" position="center,center" size="700,520" title="Object-Config-Overview">
			<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="422,10" zPosition="1" size="35,25" pixmap="skin_default/buttons/key_menu.png" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="labels" render="Listbox" scrollbarMode="showOnDemand" position="5,45" size="690,40" zPosition="3" transparent="1" >
				<convert type="TemplatedMultiContent">
					{"template": [
							MultiContentEntryText(pos = (0, 0), size = (506, 24), font = 0, flags = RT_HALIGN_LEFT, text = 1), # Name,
						],
					"fonts": [gFont("Regular", 20)],
					"itemHeight": 24
					}
				</convert>
			</widget>
			<widget name="config" position="5,85" size="690,330" scrollbarMode="showOnDemand" />
			<ePixmap position="0,410" size="700,2" pixmap="skin_default/div-h.png" zPosition="1" />
			<widget source="info" render="Label" position="5,415" size="690,50" font="Regular;21"/>
			<widget source="warning" render="Label" position="5,465" size="690,50" font="Regular;21" foregroundColor="red" />
		</screen>"""
	def __init__(self, session, xmlConfigSupportInstance, configObjectListClass, loggerInstance = None):
		try:
			Screen.__init__(self, session)
			HelpableScreen.__init__(self)
			
			self.log = loggerInstance
			if self.log == None:
				self.log = getGeneralLogger()
			
			self.objectSupport = xmlConfigSupportInstance
			self.objectSupport.objectOperationForbidden = True
			
			self.lastXmlDir = None
			self.changed = False
	
			# Button Labels
			self["key_red"] = StaticText(_("Delete"))
			self["key_green"] = StaticText(_("Save"))
			self["key_yellow"] = StaticText(_("Add"))
	
			# Create List of Entries, named config for summary
			self["config"] = configObjectListClass(self.objectSupport.getSortedTupleList(), \
				loggerInstance = self.log)
	
			self["info"] = StaticText()
			self["warning"] = StaticText()

			""" Summary
				set the setup_title in your inherited class 
			"""
			self.setup_title = "ConfigObjectOverview"
			self.onChangedEntry = []
			self["config"].onSelectionChanged.append(self.selectionChanged)
	
			# Define Actions
			self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
				{
					"ok": (self.ok, _("Edit %s") % (self.objectSupport.objectSingular)),
					"cancel": (self.cancel, _("Close and forget changes")),
				}
			)
	
			self["MenuActions"] = HelpableActionMap(self, "MenuActions",
				{
					"menu": (self.menu, _("Open Context Menu"))
				}
			)
	
			self["ChannelSelectBaseActions"] = HelpableActionMap(self, "ChannelSelectBaseActions",
				{
					"nextBouquet": (self.pageup, _("Move page up")),
					"prevBouquet": (self.pagedown, _("Move page down")),
				},
			)
			
			self["HelpActions"] = ActionMap(["HelpActions"],
				{
					"displayHelp": self.showKeyHelp,
				}
			)
			self["DirectionActions"] = HelpableActionMap(self, "DirectionActions",
				{
					"leftUp": (self.pageup, _("Move page up")),
					"rightUp": (self.pagedown, _("Move page down")),
					"up": (self["config"].up, _("Move up")),
					"down": (self.keyDown, _("Move down")),
				}, -3
			)

			self["ColorActions"] = HelpableActionMap(self, "ColorActions",
				{
					"red": (self.remove, _("Remove %s") % (self.objectSupport.objectSingular)),
					"green": (self.save, _("Close and save changes")),
					"yellow": (self.add, _("Add new Entry")),
				}
			)
			
			"""
				manipulate or extend this list for own entries
				use getBaseMenuCB() or extend menuCallback() to react
			"""
			self.menulist = [
				(_("Export %s-Configuration") % (self.objectSupport.objectPlural), self.CONST_MENU_XMLTOOL_EXPORT),
				(_("Import %s-Configuration") % (self.objectSupport.objectPlural), self.CONST_MENU_XMLTOOL_IMPORT),
				("--", None),
				(_("Show Help"), self.CONST_MENU_XMLTOOL_HELP),
			]
			
			self.onLayoutFinish.append(self.setCustomTitle)
			self.onClose.append(self.onCloseAction)
		except:
			if self.log:
				self.log.printOut("ConfigObjectOverview-Init-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
			else:
				getGeneralLogger().printOut("ConfigObjectOverview-Init-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
			self.close()

	def refresh(self):
		cur = self["config"].getCurrent()
		self["config"].setList(self.objectSupport.getSortedTupleList())
		self["config"].moveToEntry(cur)

	"""
		functions you may overwrite, if you have special functionality
	"""
	def setCustomTitle(self):
		None
	
	"""
		use e. g. a enigma-config-element to store the location permanently
	"""
	def getLastXMLDir(self):
		return self.lastXmlDir
	def saveLastXMLDir(self, dirPath):
		self.lastXmlDir = dirPath

	# for Summary
	def getCurrentEntry(self):
		if self["config"].getCurrent():
			return str(self["config"].getCurrent().name)
	def getCurrentValue(self):
		if self["config"].getCurrent():
			return str(self["config"].getCurrent().name)
	def createSummary(self):
		return SetupSummary

	def selectionChanged(self):
		try:
			for x in self.onChangedEntry:
				try:
					x()
				except Exception:
					pass
		except:
			self.log.printOut("selectionChanged-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)

	def showKeyHelp(self):
		self.session.openWithCallback(self.callHelpAction, HelpMenu, self.helpList)
	
	def pageup(self):
		self["config"].pageUp()
	def pagedown(self):
		self["config"].pageDown()
	def keyUp(self):
		self["config"].up()
	def keyDown(self):
		self["config"].down()

	def ok(self):
		current = self["config"].getCurrent()
		if current is not None:
			self.objectSupport.addObject(self.session, current, callbackfunc = self.addEditCallback, overwrite = True, writeToDisk = False)

	def add(self):
		self.objectSupport.addObject(self.session, callbackfunc = self.addEditCallback, writeToDisk = False)

	def addEditCallback(self, ret):
		if ret:
			self.changed = True
			self.refresh()

	def remove(self):
		cur = self["config"].getCurrent()
		if cur is not None:
			self.session.openWithCallback(
				self.removeCallback,
				MessageBox,
				_("Do you really want to delete \"%s\"?") % (cur.name),
			)

	def removeCallback(self, ret):
		cur = self["config"].getCurrent()
		if ret and cur:
			self.objectSupport.remove(cur)
			self.changed = True
			self.refresh()

	def _getXMLFilename(self):
		from time import localtime
		ltim = localtime()
		poststr = "_%04d%02d%02d_%02d%02d%02d" %(ltim[0],ltim[1],ltim[2],ltim[3],ltim[4],ltim[5])
		
		filename = os.path.basename(self.objectSupport.XML_CONFIG)
		return filename.replace(".xml", "") + poststr + ".xml"
	
	def getBaseMenuCB(self, ret):
		callFunc = None
		if ret == self.CONST_MENU_XMLTOOL_EXPORT:
			callFunc = self.exportConfiguration
		elif ret == self.CONST_MENU_XMLTOOL_IMPORT:
			callFunc = self.importConfiguration
		elif ret == self.CONST_MENU_XMLTOOL_HELP:
			callFunc = self.showMainHelp
		return callFunc
	
	def menu(self):
		try:
			nr = 1
			keys = []
			for entry in self.menulist:
				if entry[0] == "--":
					keys.append("")
				else:
					keys.append(str(nr))
					nr += 1
			
			self.session.openWithCallback(
				self.menuCallback,
				ChoiceBox,
				list = self.menulist, 
				keys = keys,
			)
		except:
			self.log.printOut("build context-menu-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)

	def menuCallback(self, ret):
		ret = ret and ret[1]
		if ret:
			callFunc = self.getBaseMenuCB(ret)
			if callFunc != None:
				callFunc()

	def exportConfiguration(self):
		if self.changed:
			self.session.openWithCallback(
				self.doExportConfiguration,
				MessageBox,
				_("There are unsaved changes, do you want to save %s before exporting?") % (self.objectSupport.objectPluralArticle)
			)
		else:
			self.doExportConfiguration(False)
	
	def doExportConfiguration(self, savebefore = True):
		if savebefore:
			self.save(closeOverview = False)
		if self.objectSupport.objectSelect:
			self.session.openWithCallback(self.exportConfigurationFileSelect,
				self.objectSupport.objectSelect, self.objectSupport.objects.values(), 
				self.objectSupport.objects.values(), 
				windowTitle = _("Select %s for export ...") % (self.objectSupport.objectPlural))
		else:
			self.exportConfigurationFileSelect(self.objectSupport.objects.values())
	
	def exportConfigurationFileSelect(self, configObjects = None):
		if configObjects != None and len(configObjects) > 0:
			self.session.openWithCallback(boundFunction(self.exportConfigAskFurther, configObjects), 
				LocationBox, text = _("Select Export-Location"), filename = self._getXMLFilename(),
				currDir = self.getLastXMLDir())

	"""
		extend for further handling
	"""
	def exportConfigAskFurther(self, configObjects, xmlFile = None):
		self.exportConfigurationFinal(configObjects = configObjects, \
			xmlFile = xmlFile)

	def exportConfigurationFinal(self, configObjects, xmlFile = None):
		try:
			if xmlFile != None:
				if self.objectSupport.writeXml(xmlFile, configObjects):
					self.saveLastXMLDir(os.path.dirname(xmlFile))
					self.session.open(MessageBox, _("%d %s saved to \"%s\"") \
						% (len(configObjects), self.objectSupport.objectSingular if len(configObjects) == 1 \
							else self.objectSupport.objectPlural, os.path.basename(xmlFile)), \
						MessageBox.TYPE_INFO, title = _("Export Configuration"))
				else:
					self.session.open(MessageBox, _("The Configuration couldn't be written!"), \
						MessageBox.TYPE_ERROR, title = _("Export Configuration"))
		except:
			self.log.printOut("exportConfigurationFinal-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
	
	def importConfiguration(self):
		try:
			from XMLConfigTools import selectFile
			self.log.printOut("[REALDEBUG] importConfiguration vor selectFile,startDir=%s" % str(self.getLastXMLDir()), level = ERROR_LEVEL)
			selectFile(self.session, self.importConfigFileSelected, startDir = self.getLastXMLDir(), \
				showFiles = True, matchingPattern = "(?i)^.*(?!help)\.xml$", selOnlyFiles = True)
		except:
			self.log.printOut("importConfiguration-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)

	def importConfigFileSelected(self, xmlFile = None):
		try:
			if xmlFile:
				importObjects = []
				importCount = self.objectSupport.readXml(inOutObjectList = importObjects, 
					xmlFile = xmlFile, clearExisting = False, writeToRam = False)
				if importCount > 0:
					self.saveLastXMLDir(os.path.dirname(xmlFile))
					if self.objectSupport.objectSelect:
						self.session.openWithCallback(boundFunction(self.importConfigFileLoaded, xmlFile),
							self.objectSupport.objectSelect, importObjects, importObjects, 
							windowTitle = _("Select %s for import ...") % (self.objectSupport.objectPlural))
					else:
						self.importConfigFileLoaded(importxmlFile = xmlFile, importObjects = importObjects)
				elif importCount == 0:
					self.session.open(MessageBox, _("There are no (new) entries in the configuration!"), \
						MessageBox.TYPE_INFO, title = _("Configuration-Import"))
				else:
					self.session.open(MessageBox, _("The Configuration couldn't be loaded!"), \
						MessageBox.TYPE_ERROR, title = _("Configuration-Import"))
		except:
			self.log.printOut("importConfigFileSelectedCB-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)

	def importConfigFileLoaded(self, importxmlFile = "", importObjects = None):
		if importObjects != None and len(importObjects) > 0:
			if len(self.objectSupport.objects) > 0:
				# only ask overwrite if there are persisted objects
				self.session.openWithCallback(boundFunction(self.importConfigAskOverwrite, \
					importObjects, importxmlFile), MessageBox, \
					_("Do you want to keep the existing entries?"), \
					MessageBox.TYPE_YESNO, title = _("Add or Overwrite Configuration?"), default = True)
			else:
				self.importConfigAskFurther(importObjects = importObjects, importxmlFile = importxmlFile, \
					keepExisting = False, overwriteExisting = False)

	def importConfigAskOverwrite(self, importObjects = [], importxmlFile = "", keepExisting = True):
		try:
			if keepExisting:
				askOverwrite = False
				for importObject in importObjects:
					for registeredObject in self.objectSupport.objects.values():
						if importObject.key == registeredObject.key:
							askOverwrite = True
							break
				if askOverwrite:
					self.session.openWithCallback(boundFunction(self.importConfigAskFurther, \
						importObjects, importxmlFile, keepExisting), MessageBox, \
						_("Do you want to overwrite the entries with similar name?\nIf you choose no, the matching entry of the configuration-file will not be added."), \
						MessageBox.TYPE_YESNO, title = _("Overwrite Entries?"), default = False)
				else:
					self.importConfigAskFurther(importObjects = importObjects, importxmlFile = importxmlFile, \
						keepExisting = keepExisting, overwriteExisting = False)
			else:
				self.importConfigAskFurther(importObjects = importObjects, importxmlFile = importxmlFile, \
					keepExisting = keepExisting, overwriteExisting = False)
		except:
			self.log.printOut("importConfigAskOverwrite-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
	
	"""
		extend for further handling
	"""
	def importConfigAskFurther(self, importObjects = [], importxmlFile = "", \
			keepExisting = False, overwriteExisting = False):
		self.importConfigFinal(keepExisting = keepExisting, \
			overwriteExisting = overwriteExisting, \
			importObjects = importObjects, \
			importxmlFile = importxmlFile, doImport = True)

	def importConfigFinal(self, keepExisting = False, overwriteExisting = False, \
			importObjects = [], importxmlFile = "", doImport = True):
		try:
			if doImport:
				import os
				if not keepExisting:
					self.objectSupport.clear()
				importCount = self.objectSupport.writeConfigToRam(importObjects, \
					overwriteExisting = overwriteExisting)
				if importCount > 0:
					self.changed = True
					self.refresh()
				self.session.open(MessageBox, _("%d %s loaded from \"%s\"!") \
					% (importCount, self.objectSupport.objectSingular if importCount == 1 \
						else self.objectSupport.objectPlural, os.path.basename(importxmlFile)), \
					MessageBox.TYPE_INFO, title = _("Configuration-Import"))
		except:
			self.log.printOut("importConfigFinal-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
	
	def showMainHelp(self):
		try:
			from plugin import showMainHelp
			showMainHelp(self.session)
		except:
			self.log.printOut("showMainHelp-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)

	def cancel(self):
		if self.changed:
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving %s?") % (self.objectSupport.objectPluralArticle)
			)
		else:
			self.close(False)

	def cancelConfirm(self, ret):
		if ret:
			# Invalidate config mtime to force re-read on next run
			self.objectSupport.invalidateXML()
			self.close(False)

	def save(self, closeOverview = True):
		self.objectSupport.writeXml(ignoreObjectOperationForbidden = True)
		if closeOverview:
			self.close(self.changed)
	
	def onCloseAction(self):
		self.objectSupport.objectOperationForbidden = False

"""
	init-params:
		xmlConfigSupportInstance	an instance of XMLConfigSupport
		configObject				the object to manipulate [or None to add a new]
		isUpdating					boolean
		objectName					name for new object
		loggerInstance				instance of GeneralLogger [optional]
	return: the modified or created object
"""
class ConfigObjectEditor(Screen, ConfigListScreen, HelpableScreen):
	skin = """<screen name="ConfigObjectEditor" title="Config-Object Editor" position="center,center" size="665,420">
		<ePixmap position="0,5" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<widget  position="0,5" size="140,40" source="key_red" render="Label" zPosition="1" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<ePixmap position="140,5" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<widget  position="140,5" size="140,40" source="key_green" render="Label" zPosition="1" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget  position="280,5" size="140,40" source="key_yellow" render="Label" zPosition="1" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget  position="280,5" size="140,40" name="keyYellowIcon" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
		<widget  position="420,5" size="140,40" source="key_blue" render="Label" zPosition="1" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget  position="420,5" size="140,40" name="keyBlueIcon" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<!-- visualize the keys which manipulate the current config entry -->
		<widget  position="620,380" size="35,25" name="VKeyIcon" pixmap="skin_default/buttons/key_text.png" transparent="1" zPosition="10" alphatest="on"/>
		<!-- for skins which have senseful icons
			<widget  position="580,380" size="35,25" name="LeftIcon" pixmap="skin_default/buttons/key_left.png" transparent="1" zPosition="10" alphatest="on"/>
			<widget  position="620,380" size="35,25" name="RightIcon" pixmap="skin_default/buttons/key_right.png" transparent="1" zPosition="10" alphatest="on"/>
		 -->
		<widget  position="5,50" size="655,190" name="config" scrollbarMode="showOnDemand" />
		<widget  position="5,235" size="625,30" source="additionalIconLabel" render="Label" zPosition="1" valign="center" halign="right" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget  position="635,240" size="25,25" name="additionalIcon" transparent="1" alphatest="on"/>
		<ePixmap position="0,265" size="665,2" pixmap="skin_default/div-h.png" zPosition="1" />
		<widget  position="5,270" size="655,75" source="help" render="Label" font="Regular;21" />
		<widget  position="5,350" size="655,70" source="warning" render="Label" font="Regular;21" foregroundColor="red" />
		<widget  position="460,590" size="1,1" name="HelpWindow" pixmap="skin_default/vkey_icon.png" transparent="1" zPosition="10" alphatest="on"/>
	</screen>"""

	def __init__(self, session, xmlConfigSupportInstance, configObject = None, \
			isUpdating = False, objectName = "", loggerInstance = None):
		try:
			self.log = loggerInstance
			if self.log == None:
				self.log = getGeneralLogger()
			
			Screen.__init__(self, session)
	
			self.objectSupport = xmlConfigSupportInstance
			if configObject == None:
				configObject = self.objectSupport.objectClass()
			
			self.isUpdating = isUpdating if isUpdating != None else False
			self.object = configObject
			self.objectName = objectName
			
			""" Summary
				set the setup_title in your inherited class 
			"""
			self.setup_title = "Config-Object Editor"
			self.onChangedEntry = []
	
			self.list = []
			ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changed)

			# Override selectionChanged --> normally the config tuples have a size bigger than 2 
			def selectionChanged():
				current = self["config"].getCurrent()
				if self["config"].current != current:
					if self["config"].current:
						self["config"].current[1].onDeselect(self.session)
					self["config"].current = current
					if current:
						current[1].onSelect(self.session)
				for x in self["config"].onSelectionChanged:
					try:
						x()
					except:
						if "log" in self:
							self.log.printOut("overwritten-selectionChanged-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
						else:
							getGeneralLogger().printOut("overwritten-selectionChanged-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)

			self["config"].selectionChanged = selectionChanged
			# other handling
			self["config"].onSelectionChanged.append(self.selectionChanged)
			
			self["warning"] = StaticText()
			
			self["key_red"] = StaticText(_("Cancel"))
			self["key_green"] = StaticText(_("OK"))
			self["key_yellow"] = StaticText()
			self["keyYellowIcon"] = Pixmap()
			self["key_blue"] = StaticText()
			self["keyBlueIcon"] = Pixmap()
	
			self["help"] = StaticText()
			self["LeftIcon"] = Pixmap()
			self["RightIcon"] = Pixmap()
			self["VKeyIcon"] = Pixmap()
			self["HelpWindow"] = Pixmap()
			self["LeftIcon"].hide()
			self["RightIcon"].hide()
			self["VKeyIcon"].hide()
			self["VirtualKB"].setEnabled(False)
			self["HelpWindow"].hide()
			self["additionalIconLabel"] = StaticText()
			self["additionalIcon"] = Pixmap()
			self["additionalIcon"].hide()
			
			self["ColorActions"] = HelpableActionMap(self, "ColorActions",
				{
					"red": (self.keyCancel, _("Close and forget changes")),
					"green": (self.keySave, _("Close and save changes")),
				},
			)
			self["SetupActions"] = HelpableActionMap(self, "SetupActions",
				{
					"cancel": (self.keyCancel, _("Close and forget changes")),
				},
			)
			self["ChannelSelectBaseActions"] = HelpableActionMap(self, "ChannelSelectBaseActions",
				{
					"nextBouquet": (self.pageup, _("Move page up")),
					"prevBouquet": (self.pagedown, _("Move page down")),
				},
			)
	
			self["HelpActions"] = ActionMap(["HelpActions"],
				{
					"displayHelp": self.showKeyHelp,
				}
			)
			
			self.createSetup(self.object)
			self.getConfig()
			self.configureBlueButton()
			self.configureYellowButton()
			
			# Trigger change
			self.changed()
	
			self.onLayoutFinish.append(self.setCustomTitle)
		except:
			if "log" in self:
				self.log.printOut("ConfigObject-Editor-Init-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
			else:
				getGeneralLogger().printOut("ConfigObject-Editor-Init-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
			self.close(None)
	
	"""
		Here you could initiate the "NoSave"-enigma-config-elements which represent the attrs of your objects
	"""
	def createSetup(self, configObject):
		self.log.printOut("You have to implement \"createSetup\" to configure your objects!", level = ERROR_LEVEL)

	"""
		You have to return a list of getConfigListEntry-Returns
		The expected-list contains:
			Name, Enigma-configElement, HelpTxt, reloadConfig[True,False]
		you may implement a own list, but it have to include at least name and Enigma-configElement
	"""
	def getConfig(self):
		self.log.printOut("You have to implement \"getConfig\" to show the settings of your objects!", level = ERROR_LEVEL)

	"""
		functions you may extend or overwrite, if you have special functionality
	"""
	"""
	Note:
		if you want to check the values of your object before saving,
		the method "object.checkAll(session)" is called. 
		The return of the method will be displayed as error-msg
	"""
	def configureBlueButton(self):
		self["key_blue"].text = ""
		self["keyBlueIcon"].hide()
	
	def configureYellowButton(self):
		self["key_yellow"].text = ""
		self["keyYellowIcon"].hide()

	"""
		is called after selecting another config-element
	"""
	def selectionChanged(self):
		cur = self["config"].getCurrent()
		if cur:
			if len(cur) > 2:
				if cur[2] == None:
					self.updateVariableHelpText(cur[1])
				else:
					self["help"].text = cur[2]
			
			if self.__isRealConfigText(cur[1]):
				self["VKeyIcon"].show()
				self["LeftIcon"].hide()
				self["RightIcon"].hide()
			else:
				self["VKeyIcon"].hide()
				self["LeftIcon"].show()
				self["RightIcon"].show()

	"""
		is called after pressing lef-, right- or ok-Key
	"""
	def configAction(self, enigmaConfigEntry, keyNr):
		if isinstance(enigmaConfigEntry, ConfigDirectory):
			self.selectDirectory(enigmaConfigEntry, _("Select Location"))
		self.onKeyChange()
	
	"""
		if the fourth item of your list of getConfigListEntry-Returns is "reloadConfig"
	"""
	def onKeyChange(self):
		cur = self["config"].getCurrent()
		if cur:
			if len(cur) > 3 and cur[3]:
				self.getConfig()
			elif len(cur) > 2 and cur[2] == None:
				self.updateVariableHelpText(cur[1])

	"""
		to set the help-text dependend on the selcted value of the config-element
	"""
	def updateVariableHelpText(self, configelement):
		self["help"].text = ""
	
	# help functions
	def __isRealConfigText(self, configElement):
		isReal = False
		if isinstance(configElement, ConfigText) \
			and not isinstance(configElement, ConfigNumber) \
			and not isinstance(configElement, ConfigDirectory):
			isReal = True
		return isReal

	# overwrites / extends
	def handleInputHelpers(self):
		# Bug in enigma: Handling of HelpWindow shouldn't be called if the configElement isn't real "ConfigText"
		callBase = False
		if self["config"].getCurrent() is not None:
			if self.__isRealConfigText(self["config"].getCurrent()[1]):
				callBase = True
		else:
			callBase = True
		
		if callBase:
			ConfigListScreen.handleInputHelpers(self)
	
	def keyOK(self):
		ConfigListScreen.keyOK(self)
		cur = self["config"].getCurrent()
		if cur:
			self.configAction(cur[1], KEY_OK)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		cur = self["config"].getCurrent()
		if cur:
			self.configAction(cur[1], KEY_LEFT)

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		cur = self["config"].getCurrent()
		if cur:
			self.configAction(cur[1], KEY_RIGHT)

	def selectDirectory(self, configElement, screentext):
		self.session.openWithCallback(boundFunction(self.selectDirectoryCB, configElement), \
			LocationBox, screentext, "", configElement.getValue())
	
	def selectDirectoryCB(self, configElement, res):
		try:
			if res:
				configElement.setValue(res)
		except:
			self.log.printOut("directorySelected-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)

	def showKeyHelp(self):
		self.session.openWithCallback(self.callHelpAction, HelpMenu, self.helpList)
	
	def pageup(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pagedown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

	# for Summary
	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass
	def getCurrentEntry(self):
		if self["config"].getCurrent():
			return self["config"].getCurrent()[0]
	def getCurrentValue(self):
		if self["config"].getCurrent():
			return str(self["config"].getCurrent()[1].getText())
	def createSummary(self):
		return SetupSummary
	
	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving \"%s\"?") % (self.objectName), 
				title = _("Close without saving?"))
		else:
			self.close(None)

	def cancelConfirm(self, ret):
		if ret:
			self.close(None)

	def keySave(self):
		self.save()

	def save(self):
		self.checkObject()
	
	def checkObject(self):
		errMsg = None
		try:
			errMsg = self.object.checkAll(self.session)
		except TypeError:
			pass
		
		if errMsg != None and errMsg != "":
			self.session.open(MessageBox, errMsg, type = MessageBox.TYPE_ERROR)
		else:
			try:
				if not self.isUpdating and self.objectSupport.exists(self.object.key):
					# set the first char of objectSingular to uppercase
					singularArticle = self.objectSupport.objectSingular
					words = singularArticle.split(' ')
					words[0] = words[0][0].upper() + words[0][1:]
					singularArticle = ' '.join(words)
					self.session.openWithCallback(self.checkOK, MessageBox,
						_("%s \"%s\" already exists. Do you want to overwrite?") % (singularArticle, self.objectname))
				else:
					self.checkOK(True)
			except:
				self.log.printOut("ConfigObject-Editor-checkObject-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)

	def checkOK(self, ret):
		if ret:
			self.close(self.object)

"""
	Screen to select your objects for further operations
	init-params:
		xmlConfigSupportInstance	an instance of XMLConfigSupport
		availableObjects			list of your objects
		preSelectedObjects			list of your objects, which should be selected
		windowTitle					Title of the window
		filterBtnEnabled			boolean, to show the filter-Btn (switches between enabled and disabled objects)
		showDisabled				boolean to show enabled objects, automatically True if not showing filterBtn
		loggerInstance				instance of GeneralLogger [optional]
	return: list of selected objects
"""
class ConfigObjecSelect(Screen):
	skin = """<screen name="ConfigObjecSelect" title="ConfigObjecSelect" position="center,center" size="565,290">
		<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<widget  position="280,0" size="140,40" name="keyYellowIcon" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
		<widget  position="420,0" size="140,40" name="keyBlueIcon" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="list" position="5,45" size="555,240" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session, xmlConfigSupportInstance, availableObjects, preSelectedObjects = None, \
				windowTitle = None, filterBtnEnabled = True, showDisabled = True, loggerInstance = None):
		try:
			Screen.__init__(self, session)

			self.log = loggerInstance
			if self.log == None:
				self.log = getGeneralLogger()
		
			self.objectSupport = xmlConfigSupportInstance
			self.selectedObjects = {}
			if preSelectedObjects != None:
				for object in preSelectedObjects:
					self.selectedObjects[object.key] = object
			self.availableObjects = availableObjects
			self.allSelected = False
			if len(self.selectedObjects) == len(self.availableObjects):
				self.allSelected = True
			self.showDisabled = showDisabled
			self.filterBtnEnabled = filterBtnEnabled
			if not self.filterBtnEnabled:
				self.showDisabled = True
			self.windowTitle = windowTitle
			
			self["key_red"] = StaticText(_("Cancel"))
			self["key_green"] = StaticText(_("OK"))
			self["key_yellow"] = StaticText()
			self["keyYellowIcon"] = Pixmap()
			self["key_blue"] = StaticText()
			self["keyBlueIcon"] = Pixmap()
			
			self["list"] = SelectionList(None, enableWrapAround = True)
	
			self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"ok": self.toggleSelection,
				"cancel": self.close,
				"red": self.close,
				"green": self.keyClose,
				"yellow": self.toggleAll,
			}, -5)
			self["filteractions"] = ActionMap(["ColorActions"],
			{
				"blue": self.toggleFilter,
			}, -5)
	
			self.setSelection()
			self.setFilterButton()
			self.setAllButton()
	
			self.onLayoutFinish.append(self.setCustomTitle)
		except:
			if "log" in self:
				self.log.printOut("ConfigObject-Select-Init-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
			else:
				getGeneralLogger().printOut("ConfigObject-Select-Init-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
			self.close()

	def setSelection(self, selectAll = False, deselcetAll = False):
		entries = []
		index = 0
		
		for object in sorted(self.availableObjects, key=lambda object: object.name.lower()):
			if not self.showDisabled and not object.enabled:
				continue
			if selectAll or deselcetAll:
				selected = True if selectAll else False
			else:
				selected = True if self.selectedObjects.has_key(object.key) else False
			if selected:
				self.selectedObjects[object.key] = object
			elif self.selectedObjects.has_key(object.key):
				self.selectedObjects.pop(object.key)
			entries.append(SelectionEntryComponent(object.name, object, index, selected))
			index = index + 1
		
		self["list"].setList(entries)
	
	def toggleSelection(self):
		if self.allSelected:
			self.allSelected = False
			self.setAllButton()
		self["list"].toggleSelection()
		idx = self["list"].getSelectedIndex()
		entry = self["list"].list[idx][0]
		object = entry[1]
		if entry[3]:
			self.selectedObjects[object.key] = object
		elif self.selectedObjects.has_key(object.key):
			self.selectedObjects.pop(object.key)
		
	def setCustomTitle(self):
		if self.windowTitle != None:
			self.setTitle(self.windowTitle)
	
	def toggleFilter(self, reload = True):
		if self.showDisabled:
			self.showDisabled = False
			# deselect disabled objects
			for object in self.selectedObjects.values():
				if not object.enabled:
					self.selectedObjects.pop(object.key)
		else:
			self.showDisabled = True
			if self.allSelected:
				# select disabled objects
				for object in self.availableObjects:
					if not object.enabled:
						self.selectedObjects[object.key] = object
		self.setFilterButton()
		if reload:
			self.setSelection()
	
	def setFilterButton(self):
		if self.filterBtnEnabled:			
			self["filteractions"].setEnabled(True)
			if self.showDisabled:
				self["key_blue"].text = _("Only Enabled")
			else:
				self["key_blue"].text = _("Show Disabled")
		else:
			self["key_blue"].text = ""
			self["keyBlueIcon"].hide()
			self["filteractions"].setEnabled(False)

	def toggleAll(self):
		selectAll = False
		deselcetAll = False
		if self.allSelected:
			self.allSelected = False
			deselcetAll = True
		else:
			self.allSelected = True
			selectAll = True
		self.setAllButton()
		self.setSelection(selectAll, deselcetAll)
	
	def setAllButton(self):
		if self.allSelected:
			self["key_yellow"].text = _("Clear All")
		else:
			self["key_yellow"].text = _("Select All")
	
	def keyClose(self):
		try:
			list = self["list"].getSelectionsList()
		
			objectList = []
			for item in list:
				objectList.append(item[1])
			
			self.close(objectList)
		except:
			self.log.printOut("ConfigObject-Select-keyClose-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
