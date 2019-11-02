# -*- coding: UTF-8 -*-

# Calibre Enhancements add-on for NVDA
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.
#Copyright (C) 2018 Javi Dominguez <fjavids@gmail.com>

#@ Adapting the addon for changes in Caliber 4x

from .py3compatibility import *
import appModuleHandler
import addonHandler
import api
import controlTypes
import ui
import braille
import globalCommands
import scriptHandler
#@ IAccessible objects now are UIA objects. Importing from UIA but keeping names for now.
#@ from NVDAObjects.IAccessible import IAccessible
from NVDAObjects.UIA import UIA as IAccessible
#@ from NVDAObjects.IAccessible.qt   import LayeredPane
from NVDAObjects.UIA import UIA as LayeredPane
import os.path
import appModules
appModules.__path__.insert(0, os.path.abspath(os.path.dirname(__file__))) 
try:
	from .qtEditableText import QTEditableText
except:
	QTEditableText = IAccessible
appModules.__path__.pop(0)
import textInfos
from tones import beep
from os import startfile
import winUser
from speech import speakObject, pauseSpeech
from keyboardHandler import KeyboardInputGesture
from time import sleep
import re
import versionInfo
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

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		self.lastBooksCount = []
		self.oldCaret = 0
		if hasattr(settingsDialogs, 'SettingsPanel'):
			NVDASettingsDialog.categoryClasses.append(calibrePanel)

	def terminate(self):
		try:
			if hasattr(settingsDialogs, 'SettingsPanel'):
				NVDASettingsDialog.categoryClasses.remove(calibrePanel)
		except:
			pass

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if obj.role == controlTypes.ROLE_TABLECOLUMNHEADER:
			if obj.location[2] == 0:
				# Width = 0 means that the object is not visible, although if it is displayed in the objects navigator
				# TRANSLATORS: Message shown when a table header is in navigator objects but it is not visible in the screen
				obj.description = _("(hidden)")
			clsList.insert(0, EnhancedHeader)
		if obj.role == controlTypes.ROLE_EDITABLETEXT and obj.parent.role == controlTypes.ROLE_COMBOBOX and obj.previous.role == controlTypes.ROLE_LIST:
			obj.TextInfo  = obj.makeTextInfo(textInfos.POSITION_ALL)
			clsList.insert(0, TextInComboBox)
		#@ This causes a crash:
		#@ if obj.role == controlTypes.ROLE_COMBOBOX and obj.childCount == 2:
				#@ clsList.insert(0, ComboBox)
		if obj.role == controlTypes.ROLE_DATAITEM:
			obj.reportHeaders = config.conf['documentFormatting']['reportTableHeaders']
			#@ TableCells now are Dataitems but TableCell class crashes. It needs to be adapted.
			#@ clsList.insert(0, TableCell)
		try: #@ That way it can't find it anymore. Find a valid ID for this pane
			if obj.role == controlTypes.ROLE_PANE and obj.IAccessibleRole == controlTypes.ROLE_MENUBAR and obj.parent.IAccessibleRole == 1050:
				clsList.insert(0, preferencesPane)
		except AttributeError:
			pass
		if obj.role == controlTypes.ROLE_TOOLBAR and not obj.isFocusable:
			clsList.insert(0, UnfocusableToolBar)

	def event_gainFocus(self, obj, nextHandler):
		# Removes the HTML tags that appear in the name and description of some objects
		if obj.name:
			while re.search("</?\S+>", obj.name): obj.name = obj.name.replace(re.search("</?\S+>", obj.name).group(), "")
		if obj.description:
			while re.search("</?\S+>", obj.description): obj.description = obj.description.replace(re.search("</?\S+>", obj.description).group(), "")
		# Label correctly the search box
		try:
			if obj.parent.firstChild == api.getForegroundObject().getChild(2).getChild(0).getChild(0) and obj.simpleNext.role == controlTypes.ROLE_BUTTON:
				obj.name = obj.simpleNext.name
		except:
			pass
		nextHandler()

	def event_focusEntered(self, obj, nextHandler):
		if obj.role != controlTypes.ROLE_SPLITBUTTON:
			nextHandler()

	def event_foreground(self, obj, nextHandler):
		try:
			self.lastBooksCount = self._getBooksCount().split(",")
		except:
			pass
		nextHandler()

	def event_nameChange(self, obj, nextHandler):
		if obj.role == controlTypes.ROLE_STATICTEXT and obj.parent.role == controlTypes.ROLE_STATUSBAR:
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
			if controlTypes.STATE_INVISIBLE in obj.states:
				ui.message(_(
				# TRANSLATORS: message shown when search bar is not visible, change the keystroke to show search bar for the corresponding in your application
				"The search bar is not visible. Press shift+alt+f to show it."))
				return
		gesture.send()

	def script_navigateToolBar(self, gesture):
		ui.message(_("Tools bar"))
		fg = api.getForegroundObject()
		try:
			toolBar = filter(lambda o: o.role == 35, fg.children)[0]
			toolBar.show()
		except:
			# TRANSLATORS: Message shown when the object is not found
			ui.message(_("Not found"))
			return
	# TRANSLATORS: message shown in Input gestures dialog for this script
	script_navigateToolBar.__doc__ = _("Bring focus to toolbar")

	def script_booksCount(self, gesture):
		ui.message(self._getBooksCount())
	# TRANSLATORS: message shown in Input gestures dialog for this script
	script_booksCount.__doc__ = _("says the total of books in the current library view and the number of books selected")

	def _getBooksCount(self):
		fg = api.getForegroundObject()
		try:
			statusBar = filter(lambda o: o.role == controlTypes.ROLE_STATUSBAR, fg.children)[0]
		except IndexError:
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

class EnhancedHeader(IAccessible):
	pass

class TextInComboBox(IAccessible):

	def event_caret (self):
		if hasattr(self.parent, "fakeCaret"):
			return
		# Below There is a basic support that will be executed only if the class QTEditableText has not been correctly imported
		try:
			caret = self.TextInfo ._getCaretOffset()
			if caret < 0:
				caret = 0
			ch = self.TextInfo .text[caret]
			if ch in '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ ':
				ui.message(ch)
			else:
				start, end = (self.appModule.oldCaret, caret) if caret > self.appModule.oldCaret else (caret, self.appModule.oldCaret)
				if end-start > 1:
					ui.message(self.TextInfo .text[caret:].split()[0])
				else:
					ui.message(ch)
		except IndexError:
			pass
		self.appModule.oldCaret = caret

class ComboBox(QTEditableText):

	def event_valueChange(self):
		if self.value: ui.message(self.value)

class TableCell(IAccessible):

	# TRANSLATORS: category for Calibre input gestures
	scriptCategory = _("Calibre")

	def _get_nextOutsideObject(self):
		obj = self.container.next
		if obj:
			while not obj.isFocusable:
				obj = obj.next
				if not obj: return None
		return obj

	def _get_previousOutsideObject(self):
		obj = self.container.previous
		if obj:
			while not obj.isFocusable:
				obj = obj.previous
				if not obj: return None
		return obj

	def _get_focusableContainer(self):
		obj = self.container
		while not obj.isFocusable:
			obj = obj.container
			if not obj: return None
		return obj

	def _get_columnTitles(self):
		if hasattr(self.appModule, "columnTitles"):
			return self.appModule.columnTitles
		titles = []
		obj = self.parent.firstChild
		while obj.role != controlTypes.ROLE_TABLECOLUMNHEADER and obj.role != controlTypes.ROLE_TABLECELL:
			obj = obj.simpleNext
		while obj.role == controlTypes.ROLE_TABLECOLUMNHEADER:
			titles.append(obj.name)
			obj = obj.simpleNext
		# Stores this information in appModule to not have to search it again each time a cell is focused, which would cause a slowdown
		setattr(self.appModule, "columnTitles", titles)
		return titles

	def _get_inTitleColumn(self):
		try:
			if self.columnHeaderText == self.columnTitles[1]: return True
		except IndexError:
			return False
		return False

	def _get_inAuthorColumn(self):
		try:
			if self.columnHeaderText == self.columnTitles[2]: return True
		except IndexError:
			return False
		return False

	def event_gainFocus(self):
		if winUser.getKeyState(KeyboardInputGesture.fromName("Control").vkCode) in (0,1):
			try:
				self.states.remove(controlTypes.STATE_SELECTED)
			except KeyError:
				pass
		if not self.name:
			self.name = " "
		self.reportHeaders = config.conf['documentFormatting']['reportTableHeaders']
		if versionInfo.version_year*100+versionInfo.version_major >= 201802:
			config.conf['documentFormatting']['reportTableHeaders'] = True if config.conf['calibre']['reportTableHeaders'] == "st" else False
		if self.columnHeaderText and (
		(versionInfo.version_year*100+versionInfo.version_major < 201802 and config.conf['documentFormatting']['reportTableHeaders']) or (
		versionInfo.version_year*100+versionInfo.version_major >= 201802 and config.conf['calibre']['reportTableHeaders'] == "cl")):
			# Reporting table headers at classic style (used in previous versions of NVDA or in new versions if read only column headers is selected in preferences)
			if not self.inTitleColumn and not self.inAuthorColumn:
				self.description = self.columnHeaderText
		speakObject(self, controlTypes.REASON_CARET)
		braille.handler.handleGainFocus(self)

	def event_loseFocus(self):
		config.conf['documentFormatting']['reportTableHeaders'] = self.reportHeaders

	def script_headerOptions(self, gesture):
		if self.parent.simpleParent.role == controlTypes.ROLE_DIALOG: return
		obj = self.parent.getChild(1)
		while obj.name != self.columnHeaderText and obj.role == controlTypes.ROLE_TABLECOLUMNHEADER:
			obj = obj.next
		api.setNavigatorObject(obj)
		speakObject(obj)
		winUser.setCursorPos(self.location[0]+2, obj.location[1]+2)
		winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTUP,0,0,None,None)
	# TRANSLATORS: message shown in Input gestures dialog for this script
	script_headerOptions.__doc__ = _("open the context menu for settings of the current column")

	def script_bookInfo(self, gesture):
		if api.getForegroundObject().role == controlTypes.ROLE_DIALOG:
			gesture.send()
			return
		title = self.getDataFromColumn(1)
		if title: ui.message(title)
		try:
			clipboard = api.getClipData()
		except TypeError: # Specified clipboard format is not available
			clipboard = ""
		gesture.send()
		KeyboardInputGesture.fromName("tab").send() # Skip to document
		KeyboardInputGesture.fromName("applications").send() # Open context menu
		KeyboardInputGesture.fromName("downArrow").send() # Down to first item in menu: Copy to clipboard
		KeyboardInputGesture.fromName("Enter").send() # Activate menu item
		KeyboardInputGesture.fromName("escape").send() # Close dialog
		if scriptHandler.getLastScriptRepeatCount() == 1:
			ui.browseableMessage(api.getClipData(), title if title else _("Book info"))
		else:
			sleep(0.50)
			try:
				ui.message(api.getClipData())
			except PermissionError:
				pass
		try:
			sleep(0.2)
			if True or not api.copyToClip(clipboard):
				api.win32clipboard.OpenClipboard()
				api.win32clipboard.EmptyClipboard()
				api.win32clipboard.CloseClipboard()
		except (PermissionError, AttributeError):
			pass

	def script_searchBookInTheWeb(self, gesture):
		domain = "google.com"
		title = self.getDataFromColumn(1)
		author = self.getDataFromColumn(2)
		if not title or not author:
			gesture.send()
			return
		url = u'https://www.%s/search?tbm=bks&q=intitle:%s+inauthor:%s' % (domain, title, author)
		startfile(url)
	# TRANSLATORS: message shown in Input gestures dialog for this script
	script_searchBookInTheWeb.__doc__ = _("search the current book in Google")

	def getDataFromColumn(self, columnNumber):
		try:
			columnName = self.columnTitles[columnNumber]
		except IndexError:
			return ""
		if self.columnHeaderText.lower() == columnName.lower():
			return self.name
		obj = self.previous
		while obj.role == controlTypes.ROLE_TABLECELL:
			if obj.columnHeaderText.lower() == columnName.lower():
				return obj.name
			obj = obj.previous
		obj = self.next
		while obj.role == controlTypes.ROLE_TABLECELL:
			if obj.columnHeaderText.lower() == columnName.lower():
				return obj.name
			obj = obj.next
		return ""

	def script_skipNextOutside(self, gesture):
		obj = self.nextOutsideObject
		while obj:
			if obj.isFocusable:
				api.setFocusObject(obj)
				if controlTypes.STATE_FOCUSED in obj.states: return # The object has received the focus correctly
			obj = obj.next
		# Has not been able to get out of the table
		if self.container.simpleParent.role == controlTypes.ROLE_DIALOG:
			# If we are in a dialogue, focus on the top panel
			api.setNavigatorObject(self.focusableContainer)
			scriptHandler.executeScript(globalCommands.commands.script_review_activate, None)
			pauseSpeech(True)
			return
		gesture.send()

	def script_skipPreviousOutside(self, gesture):
		obj = self.previousOutsideObject
		while obj:
			if obj.isFocusable:
				api.setFocusObject(obj)
				if controlTypes.STATE_FOCUSED in obj.states: return
			obj = obj.previous
		if self.container.simpleParent.role == controlTypes.ROLE_DIALOG:
			api.setNavigatorObject(self.focusableContainer)
			scriptHandler.executeScript(globalCommands.commands.script_review_activate, None)
			pauseSpeech(True)
			return
		gesture.send()

	__gestures = {
	"kb:NVDA+Control+H": "headerOptions",
	"kb:I": "bookInfo",
	"kb:F12": "searchBookInTheWeb",
	"kb:Control+Tab": "skipNextOutside",
	"kb:Shift+Control+Tab": "skipPreviousOutside"
	}

class preferencesPane(LayeredPane):
	tabItems = []
	focusedWidget = None

	def __updateTab(self, index):
		if self.focusedWidget:
			return
		fg = api.getForegroundObject()
		max = len(self.tabItems)-1
		index = 0 if index > max else max if index < 0 else index
		setattr(fg, "tabIndex", index)
		self.name = self.tabItems[fg.tabIndex].name
		speakObject(self)

	def event_gainFocus(self):
		isMultitab = False
		ch = self.simpleFirstChild
		while ch:
			if ch.IAccessibleRole == controlTypes.ROLE_TAB:
				isMultitab = True
				break
			ch = ch.next
		try:
			if isMultitab: self.tabItems = filter(lambda i: i.IAccessibleRole == controlTypes.ROLE_HEADING1 and i.next.IAccessibleRole == controlTypes.ROLE_TAB, self.recursiveDescendants)
		except AttributeError:
			self.tabItems = []
		if self.tabItems:
			self.role = controlTypes.ROLE_TAB
			fg = api.getForegroundObject()
			if not hasattr(fg, "tabIndex"):
				setattr(fg, "tabIndex", 0)
			self.__updateTab(fg.tabIndex)
		else:
			try:
				if self.simpleFirstChild.IAccessibleRole == controlTypes.ROLE_HEADING1:
					self.name = self.simpleFirstChild.name
			except AttributeError:
				pass
			self.name = self.simpleParent.name if not self.name and self.simpleParent.role == 4 else self.name
			speakObject(self)

	def __skipToTab(self, skip):
		if not self.tabItems:
			return False
		fg = api.getForegroundObject()
		self.__updateTab(fg.tabIndex+skip)
		return True

	def script_nextTab(self, gesture):
		if not self.__skipToTab(+1): gesture.send()

	def script_previousTab(self, gesture):
		if not self.__skipToTab(-1): gesture.send()

	def script_nextTab_(self, gesture):
		self.focusedWidget = None
		if not self.__skipToTab(+1): gesture.send()

	def script_previousTab_(self, gesture):
		self.focusedWidget = None
		if not self.__skipToTab(-1): gesture.send()

	def script_nextWidget(self, gesture):
		if not self.tabItems:
			KeyboardInputGesture.fromName("tab").send()
			return
		fg = api.getForegroundObject()
		if not self.focusedWidget:
			self.focusedWidget = self.tabItems[fg.tabIndex].next.simpleFirstChild
		else:
			self.focusedWidget = self.focusedWidget.simpleNext
		if self.focusedWidget:
			api.setNavigatorObject(self.focusedWidget)
			speakObject(self.focusedWidget)
		else:
			# gesture.send()
			KeyboardInputGesture.fromName("tab").send()

	def script_previousWidget(self, gesture):
		if not self.focusedWidget:
			KeyboardInputGesture.fromName("shift+tab").send()
			return
		self.focusedWidget = self.focusedWidget.simplePrevious
		if self.focusedWidget:
			api.setNavigatorObject(self.focusedWidget)
			speakObject(self.focusedWidget)
		else:
			api.setNavigatorObject(self)
			speakObject(self)

	def script_doAction(self, gesture):
		if self.focusedWidget:
			self.focusedWidget.doAction()

	__gestures = {
	"kb:rightArrow": "nextTab",
	"kb:leftArrow": "previousTab",
	"kb:Tab": "nextWidget",
	"kb:Shift+Tab": "previousWidget",
	"kb:Control+Tab": "nextTab_",
	"kb:Shift+Control+Tab": "previousTab_",
	"kb:downArrow": "nextWidget",
	"kb:upArrow": "previousWidget",
	"kb:Enter": "doAction",
	"kb:Space": "doAction"
	}

class UnfocusableToolBar(IAccessible):

	returnFocusTo = None

	def event_loseFocus(self):
		ui.message (_("Leaving the toolbar"))

	def script_next(self, gesture):
		obj = api.getNavigatorObject()
		if obj.parent == self:
			obj = obj.next if obj.next else self.firstChild
			while obj.actionCount == 0 and obj.role != controlTypes.ROLE_BUTTON:
				obj = obj.next if obj.next else self.firstChild
			self._setFakeFocus(obj)
		else:
			self._setFakeFocus(self.simpleFirstChild)

	def script_previous(self, gesture):
		obj = api.getNavigatorObject()
		if obj.parent == self:
			obj = obj.previous if obj.previous else self.lastChild
			while obj.actionCount == 0 and obj.role != controlTypes.ROLE_BUTTON:
				obj = obj.previous if obj.previous else self.lastChild
			self._setFakeFocus(obj)
		else:
			self._setFakeFocus(self.simpleFirstChild)

	def script_doAction(self, gesture):
		obj = api.getNavigatorObject()
		if obj.parent == self:
			if obj.actionCount >0:
				scriptHandler.executeScript(globalCommands.commands.script_review_activate, KeyboardInputGesture)
			else:
				scriptHandler.executeScript(self.script_menu, None)
		else:
			beep(200, 80)

	def script_menu(self, gesture):
		obj = api.getNavigatorObject()
		if obj.parent == self and controlTypes.STATE_INVISIBLE not in obj.states:
			scriptHandler.executeScript(globalCommands.commands.script_moveMouseToNavigatorObject, None)
			pauseSpeech(True)
			x, y = winUser.getCursorPos()
			if x >= obj.location[0]:
				winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN,0,0,None,None)
				winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTUP,0,0,None,None)
			else:
				# TRANSLATORS: Message when it can't click in a item of the toolbar
				ui.message(_("Can't click in %s, try to maximize the window") % (obj.name if obj.name else controlTypes.roleLabels[obj.role]))
		else:
			beep(200,80)

	def script_exit(self, gesture):
		if self.returnFocusTo:
			api.setFocusObject(self.returnFocusTo)
		else:
			api.setFocusObject(api.getForegroundObject())

	def show(self):
		self.returnFocusTo = api.getFocusObject()
		api.setFocusObject(self)
		self._setFakeFocus(self.simpleFirstChild)

	def _setFakeFocus(self, obj):
		api.setNavigatorObject(obj)
		if controlTypes.STATE_INVISIBLE in obj.states:
			obj.states.remove(controlTypes.STATE_INVISIBLE )
		speakObject(obj)

	__gestures = {
	"kb:escape": "exit",
	"kb:rightArrow": "next",
	"kb:downArrow": "next",
	"kb:Tab": "next",
	"kb:leftArrow": "previous",
	"kb:upArrow": "previous",
	"kb:Shift+Tab": "previous",
	"kb:Enter": "doAction",
	"kb:Space": "doAction",
	"kb:applications": "menu"
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
