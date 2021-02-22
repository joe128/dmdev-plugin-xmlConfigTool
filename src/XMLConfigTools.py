# -*- coding: utf-8 -*-

from Plugins.SystemPlugins.GeneralLogger.GeneralLogger import OutLogger, ERROR_LEVEL, WARN_LEVEL, DEBUG_LEVEL
from traceback import format_exc

PLUGIN_VERSION = "0.1b1"

# -- File-Dialog
from Screens.Screen import Screen

from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.Button import Button
from Components.FileList import FileList

from . import _

generalLogger = None
def getGeneralLogger(additionalPrefix = ""):
	global generalLogger
	if generalLogger == None:
		prefix = "XMLConfigTool"
		if additionalPrefix and additionalPrefix != "":
			prefix += " %s" % additionalPrefix
		generalLogger = OutLogger(prefix = prefix, inPluginVersion = PLUGIN_VERSION)
	return generalLogger

class selectFileDlg(Screen):
	skin = """
		<screen name="selectFileDlg" position="center,center" size="700,450">
			<widget name="filelist" position="10,10" size="680,300" scrollbarMode="showOnDemand" />
			<widget name="key_green_text" position="70,360" size="600,25" halign="left" zPosition="10" font="Regular;21" transparent="1" />
			<widget name="button_green" pixmap="skin_default/buttons/button_green.png" position="30,360" zPosition="10" size="35,25" transparent="1" alphatest="on" />
			<widget name="key_red_text" position="70,390" size="270,25" halign="left" zPosition="10" font="Regular;21" transparent="1" />
			<widget name="button_red" pixmap="skin_default/buttons/button_red.png" position="30,390" zPosition="10" size="35,25" transparent="1" alphatest="on" />
			<widget name="key_blue_text" position="420,390" size="270,25" halign="left" zPosition="10" font="Regular;21" transparent="1" />
			<widget name="button_blue" pixmap="skin_default/buttons/button_blue.png" position="380,390" zPosition="10" size="35,25" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, startDir = None, showDirectories = True, showFiles = False, \
			showMountpoints = True, matchingPattern = None, useServiceRef = False, \
			inhibitDirs = False, inhibitMounts = False, isTop = False, enableWrapAround = False, \
			additionalExtensions = None, selOnlyFiles = False, permanentBookmark = None, \
			loggerInstance = None):
		try:
			Screen.__init__(self, session)
			self.session = session
			self.selOnlyFiles = selOnlyFiles
			self.showFiles = showFiles
			if self.selOnlyFiles:
				self.showFiles = True
			self.epath = ""

			self.log = loggerInstance
			if self.log == None:
				self.log = getGeneralLogger()
	
			self["button_green"] = Pixmap()
			self["key_green_text"] = Button()
			self["button_red"] = Pixmap()
			self["key_red_text"] = Label(_("Close"))
			self["button_blue"] = Pixmap()
			self["key_blue_text"] = Button()
			if startDir == None or startDir == "":
				startDir = "/media/hdd"
			
			self["filelist"] = FileList(directory = startDir, showDirectories = showDirectories, \
				showFiles = self.showFiles, showMountpoints = showMountpoints, \
				matchingPattern = matchingPattern, useServiceRef = useServiceRef, \
				inhibitDirs = inhibitDirs, inhibitMounts = inhibitMounts, isTop = isTop, \
				enableWrapAround = enableWrapAround, additionalExtensions = additionalExtensions)
			self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions"],
			{
				"ok": self.ok,
				"back": self.cancel,
				"left": self.left,
				"right": self.right,
				"up": self.up,
				"down": self.down,
				"green": self.green,
				"red": self.red,
				"blue": self.goToPermanentBookmark,
			}, -1)
			
			if permanentBookmark != None and not isinstance(permanentBookmark, dict):
				permanentBookmark = None
			self.permanentBookmark = permanentBookmark
			self.configureBlueButton()
	
			self.onLayoutFinish.append(self.setStartDir)
		except:
			if self.log == None:
				self.log.printOut("selectFileDlg-Init-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
			else:
				getGeneralLogger().printOut("selectFileDlg-Init-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
			self.close(None)

	def configureBlueButton(self):
		try:
			if self.permanentBookmark != None and self.permanentBookmark.keys()[0] != self["filelist"].getCurrentDirectory():
				self["key_blue_text"].setText(self.permanentBookmark.values()[0])
				self["button_blue"].show()
			else:
				self["key_blue_text"].text = ""
				self["button_blue"].hide()
		except:
			self.log.printOut("configureBlueButton-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
	
	def goToPermanentBookmark(self):
		try:
			if self.permanentBookmark != None:
				self["filelist"].changeDir(self.permanentBookmark.keys()[0])
				self.updatePathName()
		except:
			self.log.printOut("goToPermanentBookmark-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)

	def setWindowTitle(self):
		if self.instance and self["filelist"].getCurrentDirectory():
			self.instance.setTitle(self["filelist"].getCurrentDirectory())
	
	def setStartDir(self):
		try:
			try:
				if self["filelist"].canDescent():
					self["filelist"].descent()
			except:
				self.log.printOut("setStartDir-inner-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)	
			self.setWindowTitle()
			self.setPathName()
		except:
			self.log.printOut("setStartDir-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)

	def updatePathName(self):
		# getFilename is None if e.g. device-list is selected
		if self.showFiles or (self["filelist"].getFilename() and len(self["filelist"].getFilename()) > len(self["filelist"].getCurrentDirectory())):
			self.setPathName()
		else:
			self["key_green_text"].hide()
			self["button_green"].hide()
		self.setWindowTitle()
		self.configureBlueButton()

	def setPathName(self):
		if self.showFiles and self["filelist"].canDescent() == False:
			self.fileName = self["filelist"].getFilename()
			self.epath = self["filelist"].getCurrentDirectory() + "/" + self["filelist"].getFilename()
		else:
			self.fileName = ""
			self.epath = self["filelist"].getCurrentDirectory()
		if len(self.epath) > 1 and self.epath.endswith('/'):
			self.epath = self.epath[:-1]
		if self.selOnlyFiles:
			if self.fileName == "":
				self["key_green_text"].setText(_("select a valid file"))
			else:
				self["key_green_text"].setText(_("select: %s") % (self.fileName))
		else:
			self["key_green_text"].setText(_("select: %s") % (self.epath))
		self["key_green_text"].show()
		self["button_green"].show()

	def ok(self):
		if self["filelist"].canDescent():
			self["filelist"].descent()
			if self["filelist"].getFilename() != None and self["filelist"].getCurrentDirectory() != None:
				if len(self["filelist"].getFilename()) > len(self["filelist"].getCurrentDirectory()):
					self.setPathName()
				else:
					self["key_green_text"].hide()
					self["button_green"].hide()
				self.setWindowTitle()
			self.updatePathName()
		else:
			if self.selOnlyFiles and self.fileName != "":
				self.close(self.epath)

	def up(self):
		self["filelist"].up()
		self.updatePathName()

	def down(self):
		self["filelist"].down()
		self.updatePathName()

	def left(self):
		self["filelist"].pageUp()
		self.updatePathName()

	def right(self):
		self["filelist"].pageDown()
		self.updatePathName()

	def cancel(self):
		self.close(False)

	def red(self):
		self.close(False)

	def green(self):
		if not self.selOnlyFiles or self.fileName != "":
			self.close(self.epath)

def selectFile(session, callback, startDir = None, showFiles = False, matchingPattern = None, \
		selOnlyFiles = False, permanentBookmark = None, loggerInstance = None):
	session.openWithCallback(callback, selectFileDlg, startDir = startDir, showFiles = showFiles, \
			matchingPattern = matchingPattern, selOnlyFiles = selOnlyFiles, \
			permanentBookmark = permanentBookmark, loggerInstance = loggerInstance)

