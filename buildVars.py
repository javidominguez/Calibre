# -*- coding: UTF-8 -*-

# Build customizations
# Change this file instead of sconstruct or manifest files, whenever possible.

import os, glob

if os.path.exists(os.path.join(os.getcwd(), "addon\\manifest.ini")):
	os.remove(os.path.join(os.getcwd(), "addon\\manifest.ini"))
for d in glob.glob(os.path.join(os.getcwd(), "addon\\doc\\*")):
	if os.path.isdir(d):
		for h in glob.glob(os.path.join(d, "readme.html")):
			os.remove(h)

def tagBuild (v="", minutes=False):
	if v and "dev" not in v.lower(): return str(v)
	from datetime import datetime
	today = datetime.now()
	return "%s%s.%s" % (v, today.year*10000+today.month*100+today.day, today.hour*60+today.minute) if minutes else "%s%s" % (v, today.year*10000+today.month*100+today.day)

# Full getext (please don't change)
_ = lambda x : x

# Add-on information variables
addon_info = {
	# for previously unpublished addons, please follow the community guidelines at:
	# https://bitbucket.org/nvdaaddonteam/todo/raw/master/guideLines.txt
	# add-on Name, internal for nvda
	"addon_name" : "calibre",
	# Add-on summary, usually the user visible name of the addon.
	# Translators: Summary for this add-on to be shown on installation and add-on information.
	"addon_summary" : _("Calibre accessibility enhancements"),
	# Add-on description
	# Translators: Long description to be shown for this add-on on add-on information from add-ons manager
	"addon_description" : _("Provides some accessibility enhancements for the interface of Calibre eBook Management"),
	# version
	"addon_version" : "1.3+PY3",
	# Author(s)
	"addon_author" : u"Javi Dominguez <fjavids@gmail.com>",
	# URL for the add-on documentation support
	"addon_url" : 'https://github.com/javidominguez/calibre',
	# File name for the add-on help file.
	"addon_docFileName" : "readme.html",
	# Minimum NVDA version supported (e.g. "2018.3")
	"addon_minimumNVDAVersion" : "2018.1.0",
	# Last NVDA version supported/tested (e.g. "2018.4", ideally more recent than minimum version)
	"addon_lastTestedNVDAVersion" : "2019.3.0",
	# Add-on update channel (default is stable or None)
	"addon_updateChannel" : None
}


import os.path

# Define the python files that are the sources of your add-on.
# You can use glob expressions here, they will be expanded.
pythonSources = [os.path.join("addon", "appModules", "*.py"),]

# Files that contain strings for translation. Usually your python sources
i18nSources = pythonSources + ["buildVars.py"]

# Files that will be ignored when building the nvda-addon file
# Paths are relative to the addon directory, not to the root directory of your addon sources.
excludedFiles = []
