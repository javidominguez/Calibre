# Calibre Enhancements add-on for NVDA
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.
#Copyright (C) 2018 Javi Dominguez <fjavids@gmail.com>

import appModuleHandler
import addonHandler
import api
import controlTypes
import ui
import globalCommands
import scriptHandler
from NVDAObjects.IAccessible import IAccessible, InaccessibleComboBox
import textInfos
from tones import beep
import os
import winUser
from speech import speakObject, pauseSpeech
from keyboardHandler import KeyboardInputGesture
from time import sleep

addonHandler.initTranslation()

class AppModule(appModuleHandler.AppModule):

	#TRANSLATORS: category for Calibre input gestures
	scriptCategory = _("Calibre")

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if obj.role == controlTypes.ROLE_TABLECOLUMNHEADER:
			if obj.location[2] == 0:
				obj.description = _("(hidden)")
			clsList.insert(0, EnhancedHeader)
		if obj.role == controlTypes.ROLE_EDITABLETEXT and obj.parent.role == controlTypes.ROLE_COMBOBOX and obj.previous.role == controlTypes.ROLE_LIST:
			obj.TextInfo  = obj.makeTextInfo(textInfos.POSITION_ALL)
			clsList.insert(0, ComboBox)
		if obj.role == controlTypes.ROLE_TABLECELL:
			clsList.insert(0, TableCell)

	def tbContextMenu(self, obj, func):
		api.setNavigatorObject(obj)
		x = obj.location[0]+2
		y = obj.location[1]+2
		winUser.setCursorPos(x, y)
		if api.getDesktopObject().objectFromPoint(x,y) == obj:
			scriptHandler.executeScript(func, None)
		else:
			ui.message(_("Not found"))

	def script_libraryMenu(self, gesture):
		fg = api.getForegroundObject()
		try:
			obj = fg.getChild(3).getChild(13)
		except AttributeError:
			ui.message(_("Not found"))
		else:
			ui.message("%s, %s" % (_("Tools bar"), obj.name))
			self.tbContextMenu(obj, globalCommands.commands.script_leftMouseClick)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_libraryMenu.__doc__ = _("open the context menu for selecting   and maintenance library")

	def script_addBooksMenu(self, gesture):
		fg = api.getForegroundObject()
		try:
			obj = fg.getChild(3).getChild(1)
		except AttributeError:
			ui.message(_("Not found"))
		else:
			ui.message("%s, %s" % (_("Tools bar"), obj.name))
			self.tbContextMenu(obj, globalCommands.commands.script_rightMouseClick)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_addBooksMenu.__doc__ = _("open the context menu for adding books")

	def script_searchMenu(self, gesture):
		fg = api.getForegroundObject()
		try:
			obj = fg.getChild(2).getChild(0).getChild(11)
		except AttributeError:
			ui.message(_("Not found"))
		else:
			ui.message("%s, %s" % (_("Search bar"), obj.name))
			self.tbContextMenu(obj, globalCommands.commands.script_rightMouseClick)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_searchMenu.__doc__ = _("open the context menu for saved searches")

	def script_virtualLibrary(self, gesture):
		fg = api.getForegroundObject()
		try:
			obj = fg.getChild(2).getChild(0).getChild(0)
		except AttributeError:
			ui.message(_("Not found"))
		else:
			ui.message("%s, %s" % (_("Search bar"), obj.name))
			self.tbContextMenu(obj, globalCommands.commands.script_leftMouseClick)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_virtualLibrary.__doc__ = _("open the context menu for virtual libraries")

	def script_navegateSearchBar(self, gesture):
		fg = api.getForegroundObject()
		obj = fg.getChild(2).getChild(0).getChild(0)
		if controlTypes.STATE_INVISIBLE in obj.states:
			ui.message(_("The search bar is not visible."))
		else:
			ui.message("%s, %s" % (_("Search bar"), obj.name))
			api.setNavigatorObject(obj)
			scriptHandler.executeScript(globalCommands.commands.script_moveMouseToNavigatorObject, None)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_navegateSearchBar.__doc__ = _("bring the objects navigator to first item on search bar")

	def script_navegateToolsBar(self, gesture):
		ui.message(_("Tools bar"))
		fg = api.getForegroundObject()
		obj = fg.getChild(3).getChild(0)
		speakObject(obj)
		api.setNavigatorObject(obj)
		scriptHandler.executeScript(globalCommands.commands.script_moveMouseToNavigatorObject, None)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_navegateToolsBar.__doc__ = _("bring the objects navigator to first item on toolbar")

	def script_nBooks(self, gesture):
		fg = api.getForegroundObject()
		try:
			obj = fg.getChild(10).getChild(2)
			pos = 2 if "[64bit]" in obj.name else 1
			ui.message(obj.name.split("[")[pos].replace("]", ""))
		except AttributeError:
			obj = fg.getChild(9).getChild(2)
			pos = 2 if "[64bit]" in obj.name else 1
			ui.message(obj.name.split("[")[pos].replace("]", ""))
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_nBooks.__doc__ = _("says the total of books in the current library view and the number of books selected")

	def script_navegateHeaders(self, gesture):
		fg = api.getForegroundObject()
		obj = fg.getChild(2).getChild(2).getChild(1).getChild(0).getChild(0).getChild(1).getChild(1).getChild(0).getChild(2)
		api.setNavigatorObject(obj)
		scriptHandler.executeScript(globalCommands.commands.script_moveMouseToNavigatorObject, None)
		ui.message(obj.name)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_navegateHeaders.__doc__ = _("bring the objects navigator to first item on table header")

	__gestures = {
	"kb:F8": "libraryMenu",
	"kb:F7": "addBooksMenu",
	"kb:F6": "searchMenu",
	"kb:F5": "virtualLibrary",
	"kb:F9": "navegateSearchBar",
	"kb:F10": "navegateToolsBar",
	"kb:NVDA+H": "navegateHeaders",
	"kb:NVDA+End": "nBooks"
	}

class EnhancedHeader(IAccessible):
	pass

class ComboBox(InaccessibleComboBox):

	def event_caret (self):
		try:
			savedSearches = [o.name for o in self.previous.children]
			if self.TextInfo.text not in savedSearches:
				caret = self.TextInfo ._getCaretOffset()
				if caret == len(self.TextInfo .text):
					caret = caret-1
				if caret < 0:
					caret = 0
				ui.message(self.TextInfo .text[caret])
		except IndexError:
			pass

class TableCell(IAccessible):

	#TRANSLATORS: category for Calibre input gestures
	scriptCategory = _("Calibre")

	def event_gainFocus(self):
		self.states.remove(controlTypes.STATE_SELECTED)
		if not self.name:
			self.name = " "
		# TRANSLATORS: Name of the columns Title and Author as shown in the interface of Calibre 
		if self.columnHeaderText.lower() != _("Title").lower() and self.columnHeaderText.lower()  != _("Author(s)").lower():
			ui.message(self.columnHeaderText)
		speakObject(self, controlTypes.REASON_CARET)

	def script_headerOptions(self, gesture):
		obj = self.parent.getChild(1)
		while obj.name != self.columnHeaderText and obj.role == controlTypes.ROLE_TABLECOLUMNHEADER:
			obj = obj.next
		obj.scrollIntoView()
		api.setNavigatorObject(obj)
		speakObject(obj)
		winUser.setCursorPos(obj.location[0], obj.location[1]+5)
		if obj.location[0] > winUser.getCursorPos()[0] or controlTypes.STATE_INVISIBLE in obj.states:
			ui.message(_("Out of screen, can't click"))
			beep(300, 90)
		else:
			winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN,0,0,None,None)
			winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTUP,0,0,None,None)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_headerOptions.__doc__ = _("open the context menu for settings of the current column")

	def script_bookInfo(self, gesture):
		if api.getForegroundObject().role == controlTypes.ROLE_DIALOG:
			gesture.send()
			return
		clipboard = api.getClipData()
		gesture.send()
		KeyboardInputGesture.fromName("tab").send()
		KeyboardInputGesture.fromName("applications").send()
		KeyboardInputGesture.fromName("t").send()
		KeyboardInputGesture.fromName("escape").send()
		sleep(0.25)
		pauseSpeech(True)
		# TRANSLATORS: Name of the column Title as shown in the interface of Calibre 
		title = self.getDataFromColumn(_("Title"))
		if scriptHandler.getLastScriptRepeatCount() == 1:
			ui.browseableMessage(api.getClipData(), title if title else _("Book info"))
		else:
			ui.message("%s\n%s" % (title, api.getClipData()))
		api.copyToClip(clipboard)

	def script_searchBookInTheWeb(self, gesture):
		# TRANSLATORS: Put the domain corresponding to your country
		domain = _("google.com")
		# TRANSLATORS: Name of the column Title as shown in the interface of Calibre
		title = self.getDataFromColumn(_("Title"))
		# TRANSLATORS: Name of the column Author as shown in the interface of Calibre 
		author = self.getDataFromColumn(_("Author(s)"))
		url = u'https://www.%s/search?tbm=bks&q=intitle:%s+inauthor:%s' % (domain, title, author)
		os.startfile(url)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_searchBookInTheWeb.__doc__ = _("search the current book in Google")

	def getDataFromColumn(self, columnName):
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

	__gestures = {
	"kb:NVDA+Control+H": "headerOptions",
	"kb:I": "bookInfo",
	"kb:F12": "searchBookInTheWeb"
	}
