# -*- coding: UTF-8 -*-

# Calibre Enhancements add-on for NVDA
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.
#Copyright (C) 2018-2020 Javi Dominguez <fjavids@gmail.com>

from .OverlayClasses import *
import appModuleHandler
import addonHandler
import api
import controlTypes
import ui
import scriptHandler
from NVDAObjects.IAccessible import IAccessible
from NVDAObjects.UIA import UIA
import textInfos
from tones import beep
from os import startfile
import winUser
from speech import speech, speakObject, pauseSpeech
import re
import config
import wx
from gui import guiHelper 
from gui import settingsDialogs
try:
	from gui import NVDASettingsDialog
	from gui.settingsDialogs import SettingsPanel
except:
	SettingsPanel = object

addonHandler.initTranslation()

confspec = {
	"reportTableHeaders":"string(default=st)"
}
config.conf.spec['calibre']=confspec

class AppModule(appModuleHandler.AppModule):

	# TRANSLATORS: category for Calibre input gestures
	scriptCategory = _("Calibre")

	speechOnDemand = {"speakOnDemand": True} if hasattr(speech.SpeechMode, "onDemand") else {}

	def _get_productName(self):
		return "Calibre"

	def _get_productVersion(self):
		return _("unknown")

	def _get_statusBar(self):
		fg = api.getForegroundObject()
		if fg.APIClass == UIA:
			sb = filter(lambda o: o.UIAElement.currentClassName == "StatusBar", fg.children)
			try:
				return next(sb)
			except:
				pass
		return None

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		self.lastBooksCount = []
		self.oldCaret = 0
		self.lastRowHeader = ""
		self.lastColumnHeader = ""
		if hasattr(settingsDialogs, 'SettingsPanel'):
			NVDASettingsDialog.categoryClasses.append(calibrePanel)

	def terminate(self):
		try:
			if hasattr(settingsDialogs, 'SettingsPanel'):
				NVDASettingsDialog.categoryClasses.remove(calibrePanel)
		except:
			pass

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if obj.role == controlTypes.Role.HEADER:
			if obj.location[2] == 0:
				# Width = 0 means that the object is not visible, although if it is displayed in the objects navigator
				# TRANSLATORS: Message shown when a table header is in navigator objects but it is not visible in the screen
				obj.description = _("(hidden)")
			clsList.insert(0, UIAEnhancedHeader)
		if obj.UIAElement.currentClassName == "SearchLineEdit" and not obj.TextInfo:
			obj.TextInfo = obj.makeTextInfo(textInfos.POSITION_ALL)
			clsList.insert(0, UIATextInComboBox)
		if obj.UIAElement.currentClassName == "SearchBox2":
			clsList.insert(0, UIAComboBox)
		if obj.role == controlTypes.Role.DATAITEM:
			obj.reportHeaders = config.conf['documentFormatting']['reportTableHeaders']
			clsList.insert(0, UIATableCell)
		try:
			if obj.UIAElement.currentClassName == "Browser" and obj.parent.parent.UIAElement.currentClassName == "Preferences":
				clsList.insert(0, UIApreferencesPane)
		except AttributeError:
			pass
		try:
			if self.productVersion and re.match("4\.", self.productVersion) and obj.UIAElement.currentClassName == "QScrollArea" and obj.simpleParent.UIAElement.currentClassName == "Preferences":
				clsList.insert(0, UIAConfigWidget)
		except AttributeError:
			pass
		if obj.UIAElement.currentClassName == "ToolBar" and not obj.isFocusable:
			clsList.insert(0, UIAUnfocusableToolBar)
		if obj.UIAElement.currentClassName == "BookInfo":
			clsList.insert(0, BookInfoDialog)
		try:
			if obj.parent.parent.parent.UIAElement.currentClassName == "BookInfo":
				if obj.UIAElement.currentClassName == "Details":
					clsList.insert(0, BookInfoDetails)
				else:
					clsList.insert(0, BookInfoWindowItem)
			elif obj.UIAElement.currentClassName == "Cover":
				clsList.insert(0, BookInfoCover)
		except AttributeError:
			pass

	def event_gainFocus(self, obj, nextHandler):
		# Removes the HTML tags that appear in the name and description of some objects
		if obj.name:
			while re.search("</?\S+>", obj.name): obj.name = obj.name.replace(re.search("</?\S+>", obj.name).group(), "")
		if obj.description:
			while re.search("</?\S+>", obj.description): obj.description = obj.description.replace(re.search("</?\S+>", obj.description).group(), "")
		# Label correctly the search box
		try:
			if obj.APIClass == IAccessible:
				if obj.parent.firstChild == api.getForegroundObject().getChild(2).getChild(0).getChild(0) and obj.simpleNext.role == controlTypes.Role.BUTTON:
					obj.name = obj.simpleNext.name
			if obj.APIClass == UIA:
				if obj.UIAElement.currentClassName == "SearchBox2" and obj.simpleNext.role == controlTypes.Role.BUTTON:
					obj.name = obj.simpleNext.name
		except:
			pass
		nextHandler()

	def event_focusEntered(self, obj, nextHandler):
		if obj.APIClass == UIA and obj.UIAElement.currentClassName == "BookInfo":
			api.setForegroundObject(obj)
			nextHandler()
		if obj.role != controlTypes.Role.SPLITBUTTON:
			nextHandler()

	def event_foreground(self, obj, nextHandler):
		try:
			self.lastBooksCount = self._getBooksCount().split(",")
		except:
			pass
		# get calibre version
		if not self.productVersion and not self.productName:
			try:
				statusBar = next(filter(lambda o: o.role == controlTypes.Role.STATUSBAR, obj.children))
				statusBarText = " ".join([obj.name for obj in statusBar.children])
				productInfo = re.search(r"calibre \d\.\d+\.\d+", statusBarText)
				if productInfo:
					self.productName, self.productVersion = productInfo.group().split()
			except:
				pass
		nextHandler()

	def event_nameChange(self, obj, nextHandler):
		if obj.role == controlTypes.Role.STATICTEXT and obj.parent.role == controlTypes.Role.STATUSBAR:
			try:
				booksCount = self._getBooksCount().split(",")
			except:
				booksCount = self.lastBooksCount
			else:
				if len(booksCount) == len(self.lastBooksCount):
					for i in range(0, len(booksCount)):
						if booksCount[i] != self.lastBooksCount[i]:
							ui.message(booksCount[i])
				else:
					ui.message(",".join(booksCount))
			self.lastBooksCount = booksCount
		nextHandler()

	def event_stateChange(self, obj, nextHandler):
		if obj.UIAElement.currentClassName == "QToolBarExtension" and api.getFocusObject().role == controlTypes.Role.TOOLBAR:
			if controlTypes.State.CHECKED in obj.states:
				ui.message(_("Expanded toolbar"))
			else:
				ui.message(_("Collapsed toolbar"))
		nextHandler()

	def tbContextMenu(self, obj, func):
		api.setNavigatorObject(obj)
		x = obj.location[0]+2
		y = obj.location[1]+2
		winUser.setCursorPos(x, y)
		if api.getDesktopObject().objectFromPoint(x,y) == obj:
			scriptHandler.executeScript(func, None)
		else:
			# TRANSLATORS: Message shown when the object is not found
			ui.message(_("Not found"))

	def script_search(self, gesture):
		fg = api.getForegroundObject()
		try:
			obj = fg.getChild(2).getChild(0)
		except:
			pass
		else:
			if controlTypes.State.INVISIBLE in obj.states:
				ui.message(_(
				# TRANSLATORS: message shown when search bar is not visible, change the keystroke to show search bar for the corresponding in your application
				"The search bar is not visible. Press shift+alt+f to show it."))
				return
		gesture.send()

	def script_navigateToolBar(self, gesture):
		ui.message(_("Tools bar"))
		fg = api.getForegroundObject()
		try:
			toolBar = next(filter(lambda o: o.role == controlTypes.Role.TOOLBAR, fg.children))
			toolBar.show()
		except StopIteration:
			# TRANSLATORS: Message shown when the object is not found
			ui.message(_("Not found"))
			return
	# TRANSLATORS: message shown in Input gestures dialog for this script
	script_navigateToolBar.__doc__ = _("Bring focus to toolbar")

	@scriptHandler.script(**speechOnDemand)
	def script_booksCount(self, gesture):
		ui.message(self._getBooksCount())
	# TRANSLATORS: message shown in Input gestures dialog for this script
	script_booksCount.__doc__ = _("says the total of books in the current library view and the number of books selected")

	def _getBooksCount(self):
		fg = api.getForegroundObject()
		try:
			statusBar = next(filter(lambda o: o.role == controlTypes.Role.STATUSBAR, fg.children))
		except StopIteration:
			raise Exception("Filter has failed; statusBar not found")
		obj = statusBar.firstChild
		while obj:
			try:
				if re.match(".*[Cc]alibre.*Kovid\sGoyal.*\[", obj.name):
					break
			except TypeError:
				pass
			obj = obj.next
		try:
			return re.search("\[[^\[\]]*[0,].*\]", obj.name).group()[1:-1]
		except AttributeError:
			raise Exception("The search expression is not found in the status bar")

	__gestures = {
	"kb:Control+F": "search",
	"kb:F10": "navigateToolBar",
	"kb:NVDA+Alt+End": "booksCount"
	}

class calibrePanel(SettingsPanel):

	title=_("Calibre")

	def makeSettings(self, sizer):
		helper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# TRANSLATORS: Preferences of table headers reading
		labelText = _("Report table headers")
		self.tableHeaders = helper.addLabeledControl(labelText, wx.Choice, choices=[_("None"), _("Rows and columns"), _("Columns only")])
		self.tableHeaders.SetSelection(("no", "st", "cl").index(config.conf["calibre"]["reportTableHeaders"]))

		sizer.Add(helper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)

	def onSave(self):

		config.conf["calibre"]["reportTableHeaders"] = ("no", "st", "cl")[self.tableHeaders.GetSelection()]
