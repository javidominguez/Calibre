# -*- coding: UTF-8 -*-

# Calibre Enhancements add-on for NVDA
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.
#Copyright (C) 2019 Javi Dominguez <fjavids@gmail.com>

# OverlayClasses for Calibre 4.x

from .py3compatibility import *
import appModuleHandler
import addonHandler
import api
import controlTypes
import ui
import braille
import globalCommands
import scriptHandler
from NVDAObjects.UIA import UIA, UIColumnHeader, ComboBoxWithoutValuePattern, UIItem
import os.path
import appModules
appModules.__path__.insert(0, os.path.abspath(os.path.dirname(__file__))) 
try:
	from .qtEditableText import QTEditableText
except:
	QTEditableText = UIA
appModules.__path__.pop(0)
import textInfos
from tones import beep
from os import startfile
import winUser
from speech import speakObject, speakText, pauseSpeech
from keyboardHandler import KeyboardInputGesture
from time import sleep
import config

addonHandler.initTranslation()

class UIAEnhancedHeader(UIColumnHeader):
	pass

class UIATextInComboBox(ComboBoxWithoutValuePattern):

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

class UIAComboBox(QTEditableText):

	def event_valueChange(self):
		if self.value: ui.message(self.value)

class UIATableCell(UIItem):

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
		obj = self.table.firstChild
		while obj.role != controlTypes.ROLE_HEADER and obj.role != controlTypes.ROLE_DATAITEM:
			obj = obj.simpleNext
		while obj.role == controlTypes.ROLE_HEADER:
			titles.append(obj.name)
			obj = obj.simpleNext
		# Stores this information in appModule to not have to search it again each time a cell is focused, which would cause a slowdown
		setattr(self.appModule, "columnTitles", titles)
		return titles

	def event_gainFocus(self):
		rowHeaderText = ""
		columnHeaderText = ""
		if config.conf['calibre']['reportTableHeaders'] == "st":
			if self.rowHeaderText != self.appModule.lastRowHeader:
				rowHeaderText = "%s; " % self.rowHeaderText
			if self.columnHeaderText != self.appModule.lastColumnHeader:
				columnHeaderText = "; %s" % self.columnHeaderText
		if config.conf['calibre']['reportTableHeaders'] == "cl" and\
		self.columnHeaderText != self.appModule.lastColumnHeader:
			columnHeaderText = "; %s" % self.columnHeaderText
		speakText("%s%s%s" % (rowHeaderText, self.name, columnHeaderText))
		braille.handler.handleGainFocus(self)
		self.appModule.lastRowHeader = self.rowHeaderText
		self.appModule.lastColumnHeader = self.columnHeaderText

	def script_headerOptions(self, gesture):
		if self.parent.simpleParent.role == controlTypes.ROLE_DIALOG: return
		obj = self.table.simpleFirstChild
		while obj.name != self.columnHeaderText and obj.role == controlTypes.ROLE_HEADER:
			obj = obj.next
		api.setNavigatorObject(obj)
		winUser.setCursorPos(self.location[0]+2, obj.location[1]+2)
		winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTUP,0,0,None,None)
		KeyboardInputGesture.fromName("downArrow").send()
	# TRANSLATORS: message shown in Input gestures dialog for this script
	script_headerOptions.__doc__ = _("open the context menu for settings of the current column")

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
	"kb:Control+Tab": "skipNextOutside",
	"kb:Shift+Control+Tab": "skipPreviousOutside"
	}

class UIApreferencesPane(UIA):
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
		ch = self.firstChild.firstChild.firstChild
		while ch:
			if ch.UIAElement.currentClassName == "Category":
				isMultitab = True
				break
			ch = ch.next
		try:
			if isMultitab: self.tabItems = filter(lambda i: i.UIAElement.currentClassName == "QLabel" and i.parent.UIAElement.currentClassName == "Category", self.recursiveDescendants)
		except AttributeError:
			self.tabItems = []
		if self.tabItems:
			self.role = controlTypes.ROLE_TAB
			fg = api.getForegroundObject()
			if not hasattr(fg, "tabIndex"):
				setattr(fg, "tabIndex", 0)
			self.__updateTab(fg.tabIndex)

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

class UIAConfigWidget(UIA):

	def event_gainFocus(self):
		if self.simpleFirstChild.UIAElement.currentClassName == "QLabel":
			self.name = self.simpleFirstChild.name
		elif self.simpleNext.UIAElement.currentClassName == "QLabel":
			self.name = self.simpleNext.name
		speakObject(self)

class UIAUnfocusableToolBar(UIA):

	returnFocusTo = None

	def event_loseFocus(self):
		ui.message (_("Leaving the toolbar"))

	def script_next(self, gesture):
		obj = api.getNavigatorObject()
		if obj.parent == self:
			obj = obj.next if obj.next else self.firstChild
			while (obj.actionCount == 0 and obj.role != controlTypes.ROLE_BUTTON) or obj.role == controlTypes.ROLE_GROUPING:
				obj = obj.next if obj.next else self.firstChild
			self._setFakeFocus(obj)
		else:
			self._setFakeFocus(self.simpleFirstChild)

	def script_previous(self, gesture):
		obj = api.getNavigatorObject()
		if obj.parent == self:
			obj = obj.previous if obj.previous else self.lastChild
			while (obj.actionCount == 0 and obj.role != controlTypes.ROLE_BUTTON) or obj.role == controlTypes.ROLE_GROUPING:
				obj = obj.previous if obj.previous else self.lastChild
			self._setFakeFocus(obj)
		else:
			self._setFakeFocus(self.simpleFirstChild)

	def script_doAction(self, gesture):
		obj = api.getNavigatorObject()
		if obj.parent == self:
			if obj.actionCount >0:
				x = int(obj.location.left + obj.location.width/2)
				y = int(obj.location.top + obj.location.height/2)
				winUser.setCursorPos(x, y)
				if api.getDesktopObject().objectFromPoint(x,y) == obj:
					if winUser.getKeyState(winUser.VK_LBUTTON)&32768:
						winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
					winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,1,None,None)
					winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
			else:
				scriptHandler.executeScript(self.script_menu, None)
		else:
			beep(200, 80)

	def script_menu(self, gesture):
		obj = api.getNavigatorObject()
		if obj.parent == self and controlTypes.STATE_INVISIBLE not in obj.states and obj.role != controlTypes.ROLE_CHECKBOX:
			scriptHandler.executeScript(globalCommands.commands.script_moveMouseToNavigatorObject, None)
			pauseSpeech(True)
			x, y = winUser.getCursorPos()
			if x >= obj.location[0]:
				winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN,0,0,None,None)
				winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTUP,0,0,None,None)
				scriptHandler.executeScript(self.script_exit, None)
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

