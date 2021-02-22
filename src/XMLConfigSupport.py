# -*- coding: utf-8 -*-

# XML-Config
from xml.etree.cElementTree import parse as cet_parse
from Tools.XMLTools import stringToXML
import os

# Plugin
from Tools.BoundFunction import boundFunction
from traceback import format_exc

from XMLConfigTools import PLUGIN_VERSION, ERROR_LEVEL, WARN_LEVEL, DEBUG_LEVEL, getGeneralLogger

"""
General Support for objects, which should be stored on system via xml

xmlFilePath:			absolute Path to the xml-file on system
xmlNodeName:			XML-Node which represent the stored object
objectClass:			Class which represent the stored object
						It have to provide an attribute "key", and should be provide attributes "name" and "enabled" to use the Screens
objectEditorClass:		Screen-Class to edit the stored object (you can inherit from the class ConfigEditor)
objectSelectClass:		Screen-Class to select one or more stored objects (you can inherit from the class ConfigSelect)
[supportName]:			identifier for output-Strings, for the logger, 
						it isn't necessary if you provide an own loggerinstance
[loggerinstance]:		Instance of a General-Logger from System-Plugin
Only needed, if you want to use the screens
objectSingular			Singular-Name of your object
objectSingularArticle	Singular-Name of your object including the article
objectPlural			Plural-Name of your object
objectPluralArticle		Plural-Name of your object including the article
"""
class XMLConfigSupport:
	def __init__(self, xmlFilePath, xmlNodeName, objectClass, objectEditorClass = None, \
			objectSelectClass = None, supportName = None, loggerInstance = None, \
			objectSingular = "", objectSingularArticle = "", \
			objectPlural = "", objectPluralArticle = ""):
		self.lastConfigMtime = -1
		self.writeXMLNeeded = False
		self.objectOperationForbidden = False
		self.objects = {}
		self.objectClass = objectClass
		self.objectEditor = objectEditorClass
		self.objectSelect = objectSelectClass
		self.xmlNode = xmlNodeName
		self.XML_CONFIG = xmlFilePath
		self.xmlBool = {}
		
		self.objectSingular = objectSingular
		self.objectSingularArticle = objectSingularArticle
		self.objectPlural = objectPlural
		self.objectPluralArticle = objectPluralArticle
		
		self.log = loggerInstance
		if self.log == None:
			self.log = getGeneralLogger(additionalPrefix = supportName)
		
		# Defaults
		self.adjustBoolString("yes", "no")
	
	# functions to configure
	def adjustBoolString(self, trueValue, falseValue):
		self.xmlBool["TRUE"] = trueValue
		self.xmlBool["FALSE"] = falseValue
	# hooks
	"""
	is called before the modifying of an object
	"""
	def objectOverwritten(self, configObject, oldConfigObject):
		None
	"""
	is called if the adding or modifying of an object was successfully
	"""
	def objectAdded(self, configObject, overwrite, writeToDisk):
		None
	"""
	is called after an object is added to the objects in ram
	"""
	def objectLoaded(self, configObject, overwrite):
		None
	
	# functions you always have to implement
	"""
	You have to return a xml as list of strings, with the given objects
	"""
	def getXml(self, objectList):
		self.log.printOut("You have to implement \"getXml\" to save your objects!", level = ERROR_LEVEL)
		return None
	"""
	You have to create and return your object, from the given xml-Element
	"""
	def parseEntry(self, xmlElement):
		try:
			self.log.printOut("You have to implement \"parseEntry\" to load your objects!", level = ERROR_LEVEL)
			return self.objectClass()
		except:
			self.log.printOut("parseEntry-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
			return None
	
	# main functions
	# methods you may overwrite, if you have special functionality
	"""
	reads the content of an xml-file which contains the objects.
		returns <0 if an error occurred, 0 or the count of objects if ok
	"""
	def readXml(self, inOutObjectList = None, xmlFile = None, clearExisting = True, 
			overwriteExisting = False, writeToRam = True):
		try:
			isStandardFile = False
			if xmlFile == None:
				xmlFile = self.XML_CONFIG
				isStandardFile = True
			self.log.printOut("Read from configuration file: %s" % (str(xmlFile)), level = DEBUG_LEVEL)
			if not os.path.exists(xmlFile) or os.path.getsize(xmlFile) == 0:
				self.log.printOut("No configuration file present or file is empty!", level = WARN_LEVEL)
				return -1
	
			# Parse only if modify-time differs from the last saved in ram, 
			# and only if the file is real-xml-file
			if isStandardFile:
				mtime = os.path.getmtime(xmlFile)
				if mtime == self.lastConfigMtime:
					self.log.printOut("No changes in configuration, won't parse!", level = WARN_LEVEL)
					return 0
				# Save current mtime
				self.lastConfigMtime = mtime
	
			# Parse Config
			configuration = cet_parse(xmlFile).getroot()
	
			# Empty current Entries
			if clearExisting:
				self.clear()
			
			if inOutObjectList == None:
				inOutObjectList = []
			counter = self.parseConfig(configuration, inOutObjectList)
			if writeToRam:
				counter = self.writeConfigToRam(inOutObjectList, overwriteExisting)
			
			return counter
		except:
			self.log.printOut("readXml-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
			return -1
	
	"""
	gather the parsed objects and returns the count
	"""
	def parseConfig(self, configuration, inOutObjectList):
		counter = 0
		for xmlObject in configuration.findall(self.xmlNode):
			xobject = self.parseEntry(xmlObject)
			if xobject != None:
				inOutObjectList.append(xobject)
				counter += 1
		self.log.printOut("%d Entries parsed from config-file!" % (counter), level = DEBUG_LEVEL)
		return counter

	"""
	loads the objects to ram and returns the count
	"""	
	def writeConfigToRam(self, objectList, overwriteExisting = False):
		counter = 0
		for object in objectList:
			if object != None:
				if self.add(object, overwriteExisting):
					counter += 1
		self.log.printOut("%d Entries loaded!" % (counter), level = WARN_LEVEL)
		return counter
	
	"""
	writes the objects from ram to an xml-file.
		returns False if an error occured or the writing isn't allowed at the moment, True if ok
	"""
	def writeXml(self, xmlFile = None, objectList = None, ignoreObjectOperationForbidden = False):
		try:
			isStandardFile = False
			if xmlFile == None:
				xmlFile = self.XML_CONFIG
				isStandardFile = True
			if (isStandardFile and self.objectOperationForbidden) or ignoreObjectOperationForbidden:
				self.log.printOut("Flag objectOperationForbidden is set, writing of Config-file canceled.", level = WARN_LEVEL)
				return False
			if objectList == None:
				objectList = self.objects.values()
			xml = self.getXml(objectList)
			if xml.__sizeof__() > 0:
				with open(xmlFile, 'w') as config:
					config.writelines(xml)
				if isStandardFile:
					self.writeXMLNeeded = False
				self.log.printOut("Config-File \"%s\" written." % (str(xmlFile)), level = DEBUG_LEVEL)
			return True
		except:
			self.log.printOut("writeXml-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
			return False

	# Help-Functions
	"""
	To force a read from the XML-File
	"""
	def invalidateXML(self):
		self.lastConfigMtime = -1
	
	"""
	To get a python-bool-value from a XML-bool
		use the method adjustBoolString to configure your values
	"""
	def _xml2Bool(self, element, xmlAttr, default):
		xmlEnabled = element.get(xmlAttr, default)
		if xmlEnabled == self.xmlBool["FALSE"]:
			enabled = False
		elif xmlEnabled == self.xmlBool["TRUE"]:
			enabled = True
		else:
			self.log.printOut("Erroneous config contains invalid value for \"%s\":%s, default: %s" % (xmlAttr, xmlEnabled, default), level = ERROR_LEVEL)
			enabled = False
		return enabled
	
	"""
	To get the XML-Value for a python-bool-value
		use the method adjustBoolString to configure your values
	"""
	def _bool2Xml(self, bool):
		if bool:
			return self.xmlBool["TRUE"]
		else:
			return self.xmlBool["FALSE"]
	
	"""
	To mark the configuration as "unsafed", and write it later e.g. within a timer
	"""
	def setWriteXMLNeeded(self, needed):
		self.writeXMLNeeded = needed
	
	"""
	To lock the saving or loading of objects, e.g. while editing from the overview
		automatically set while config-screens.overview is opened
	"""
	def setObjectOperationForbidden(self, forbidden):
		self.objectOperationForbidden = forbidden
	
	"""
	To write the XML-file, only if it was marked as "unsafed" before
	"""
	def writeXmlIfNeeded(self, ignoreObjectOperationForbidden = False):
		if self.writeXMLNeeded:
			self.writeXml(ignoreObjectOperationForbidden = ignoreObjectOperationForbidden)
	
	# functions to manage the objectList in RAM
	def clear(self):
		self.objects.clear()
	
	def exists(self, objectKey):
		return objectKey in self.objects

	def get(self, objectKey):
		if objectKey in self.objects:
			return self.objects[objectKey]
		return None
		
	def add(self, object, overwrite = False):
		try:
			if not object.key in self.objects or overwrite:
				self.objects[object.key] = object
				self.objectLoaded(object, overwrite)
				return True
			return False
		except:
			self.log.printOut("add-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
	
	def remove(self, object):
		try:
			if object.key in self.objects:
				self.objects.pop(object.key)
		except:
			self.log.printOut("remove-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
	
	"""
	use this method only if the object has a name-attr
	"""
	def getSortedTupleList(self):
		list = []
		try:
			for key in sorted(self.objects, key = lambda key: self.objects[key].name.lower()):
				list.append(self.objects[key])
		except:
			self.log.printOut("getSortedTupleList-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
		return [(x,) for x in list]

	"""
	General method to add or modify an Entry
		session:		if you want to use the editor
		object:			if you want to save a modified object
		overwrite:		configure if you want to overwrite (or modify) existing objects
		writeToDisk:	if you want to write the object into the XML-file
		callbackfunc:
			given params to callback (only success, or all): 
			success [True,False] (mandatory)
			object: the modified or added object
			overwrite: loop through
			writeToDisk: loop through
	"""
	def addObject(self, session = None, object = None, callbackfunc = None, \
			overwrite = False, writeToDisk = True):
		try:
			if writeToDisk:
				# save "unsafed" values and refresh ram
				self.writeXmlIfNeeded(ignoreObjectOperationForbidden = True)
				self.readXml()
			
			oldKey = ""
			isUpdating = False
			if overwrite and object != None:
				oldKey = object.key
				isUpdating = True
			
			if session:
				session.openWithCallback(
					boundFunction(self._editorCallback, callbackfunc, overwrite, writeToDisk, oldKey),
					self.objectEditor,
					object,
					isUpdating)
			else:
				self._editorCallback(callbackfunc, overwrite, writeToDisk, oldKey, object)
		except:
			self.log.printOut("addObject-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)

	"""
	internal callback-method
	"""
	def _editorCallback(self, callbackfunc, overwrite, writeToDisk, oldKey, object):
		try:
			if object:
				if overwrite and oldKey != object.key:
					oldObject = self.get(oldKey)
					if oldObject != None:
						self.objectOverwritten(object, oldObject)
					self.remove(oldKey)
				added = self.add(object, overwrite)
				if added:
					self.objectAdded(object, overwrite, writeToDisk)
				
				if writeToDisk:
					# if called from overview then the screen is already closed, and doesn't lock the writing
					self.writeXml()
				
				if callbackfunc != None:
					try:
						callbackfunc(success = added, object = object, overwrite = overwrite, writeToDisk = writeToDisk)
					except TypeError:
						callbackfunc(added)
		except:
			self.log.printOut("addObject-editorCallback-Error:\n%s" % (str(format_exc())), level = ERROR_LEVEL)
