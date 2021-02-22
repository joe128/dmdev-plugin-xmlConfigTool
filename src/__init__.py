from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import os,gettext
 
PluginLanguageDomain = "xmlConfigTool"
PluginLanguagePath = "SystemPlugins/xmlConfigTool/locale"
# Fallback to EN for Code-Strings
DefaultPluginLang = "EN"

def localeInit():
    lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
    os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))
 
def _(txt):
    t = gettext.dgettext(PluginLanguageDomain, txt)
    if t == txt:
        t = getDefaultTxt(txt)
        if t == txt:
            t = gettext.gettext(txt)
    return t

def getDefaultTxt(txt):
    lang = language.getLanguage()[:2]
    os.environ["LANGUAGE"] = DefaultPluginLang
    t = gettext.dgettext(PluginLanguageDomain, txt)
    os.environ["LANGUAGE"] = lang
    return t
 
localeInit()
language.addCallback(localeInit)