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
from speech import speakObject

addonHandler.initTranslation()

class AppModule(appModuleHandler.AppModule):

	#TRANSLATORS: category for Calibre input gestures
	scriptCategory = _("Calibre")

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		self.muteHeaders = ()

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if obj.role == controlTypes.ROLE_TABLECOLUMNHEADER:
			if obj.location[2] == 0:
				obj.description = _("(hidden)")
			clsList.insert(0, EnhancedHeader)
		if obj.role == controlTypes.ROLE_EDITABLETEXT and obj.parent.role == controlTypes.ROLE_COMBOBOX:
			obj.textInfo = obj.makeTextInfo(textInfos.POSITION_ALL)
			clsList.insert(0, ComboBox)
		if obj.role == controlTypes.ROLE_TABLECELL:
			if not self.muteHeaders:
				fg = api.getForegroundObject()
				titleHeader =  fg.getChild(2).getChild(2).getChild(1).getChild(0).getChild(0).getChild(1).getChild(1).getChild(0).getChild(2)
				authorHeader = titleHeader.next
				self.muteHeaders = (titleHeader.name, authorHeader.name)
			obj.muteHeaders = self.muteHeaders
			clsList.insert(0, TableCell)

	def tbContextMenu(self, obj, func):
		ui.message("%s, %s" % (_("Tools bar"), obj.name))
		api.setNavigatorObject(obj)
		x = obj.location[0]+2
		y = obj.location[1]+2
		winUser.setCursorPos(x, y)
		# x, y = winUser.getCursorPos()
		if api.getDesktopObject().objectFromPoint(x,y) == obj:
			scriptHandler.executeScript(func, None)
		else:
			ui.message(_("Not found"))

	def script_libraryMenu(self, gesture):
		fg = api.getForegroundObject()
		obj = fg.getChild(3).getChild(13)
		self.tbContextMenu(obj, globalCommands.commands.script_leftMouseClick)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_libraryMenu.__doc__ = _("open the context menu for selecting   and maintenance library")

	def script_addBooksMenu(self, gesture):
		fg = api.getForegroundObject()
		obj = fg.getChild(3).getChild(1)
		self.tbContextMenu(obj, globalCommands.commands.script_rightMouseClick)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_addBooksMenu.__doc__ = _("open the context menu for adding books")

	def script_searchMenu(self, gesture):
		fg = api.getForegroundObject()
		obj = fg.getChild(2).getChild(0).getChild(11)
		self.tbContextMenu(obj, globalCommands.commands.script_rightMouseClick)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_searchMenu.__doc__ = _("open the context menu for saved searches")

	def script_virtualLibrary(self, gesture):
		fg = api.getForegroundObject()
		obj = fg.getChild(2).getChild(0).getChild(0)
		self.tbContextMenu(obj, globalCommands.commands.script_leftMouseClick)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_virtualLibrary.__doc__ = _("open the context menu for virtual libraries")

	def script_navegateToolsBar(self, gesture):
		ui.message(_("Tools bar"))
		fg = api.getForegroundObject()
		obj = fg.getChild(2).getChild(0).getChild(0)
		ui.message(obj.name)
		api.setNavigatorObject(obj)
		scriptHandler.executeScript(globalCommands.commands.script_moveMouseToNavigatorObject, None)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_navegateToolsBar.__doc__ = _("bring the objects navigator to first item on toolbar")

	def script_navegateToolsBar2(self, gesture):
		ui.message(_("Tools bar"))
		fg = api.getForegroundObject()
		obj = fg.getChild(3).getChild(0)
		speakObject(obj)
		api.setNavigatorObject(obj)
		scriptHandler.executeScript(globalCommands.commands.script_moveMouseToNavigatorObject, None)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_navegateToolsBar2.__doc__ = _("bring the objects navigator to first item on extended toolbar")

	def script_nBooks(self, gesture):
		fg = api.getForegroundObject()
		try:
			obj = fg.getChild(10).getChild(2)
			ui.message(obj.name.split("[")[1].replace("]", ""))
		except AttributeError:
			obj = fg.getChild(9).getChild(2)
			ui.message(obj.name.split("[")[1].replace("]", ""))
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

	def script_searchBookInTheWeb(self, gesture):
		obj = api.getFocusObject()
		if obj.role == controlTypes.ROLE_TABLECELL: # and (obj.simplePrevious.role == controlTypes.ROLE_TABLEROWHEADER or obj.simplePrevious.simplePrevious.role == controlTypes.ROLE_TABLEROWHEADER):
			limit = 50
			while limit and obj and obj.role != controlTypes.ROLE_TABLEROWHEADER:
				obj = obj.previous
				limit = limit - 1
			if obj:
				if obj.role == controlTypes.ROLE_TABLEROWHEADER:
					url = u'https://www.google.es/search?tbm=bks&q=intitle:%s+inauthor:%s' % (obj.next.next.name, obj.next.next.next.name)
					os.startfile(url)
					return
		beep(120, 80)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_searchBookInTheWeb.__doc__ = _("search the current book in Google")

	__gestures = {
	"kb:F8": "libraryMenu",
	"kb:F7": "addBooksMenu",
	"kb:F6": "searchMenu",
	"kb:F5": "virtualLibrary",
	"kb:F9": "navegateToolsBar",
	"kb:F10": "navegateToolsBar2",
	"kb:NVDA+H": "navegateHeaders",
	"kb:NVDA+End": "nBooks", 
	"kb:F12": "searchBookInTheWeb"
	}

class EnhancedHeader(IAccessible):
	pass

class ComboBox(InaccessibleComboBox):

	def event_caret (self):
		try:
			savedSearches = [o.name for o in self.previous.children]
			if self.value not in savedSearches:
				caret = self.textInfo._getCaretOffset()
				if caret == len(self.textInfo.text):
					caret = caret-1
				if caret < 0:
					caret = 0
				ui.message(self.textInfo.text[caret])
		except IndexError:
			pass

class TableCell(IAccessible):

	#TRANSLATORS: category for Calibre input gestures
	scriptCategory = _("Calibre")

	def event_gainFocus(self):
		self.states.remove(controlTypes.STATE_SELECTED)
		if not self.name:
			self.name = " "
		if self.columnHeaderText not in self.muteHeaders:
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
		if obj.location[0] > winUser.getCursorPos()[0]:
			ui.message(_("Out of screen, can't click"))
			beep(300, 90)
		else:
			winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN,0,0,None,None)
			winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTUP,0,0,None,None)
	#TRANSLATORS: message shown in Input gestures dialog for this script
	script_headerOptions.__doc__ = _("open the context menu for settings of the current column")

	__gestures = {
	"kb:NVDA+Control+H": "headerOptions"
	}
