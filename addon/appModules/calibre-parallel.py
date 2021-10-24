# -*- coding: UTF-8 -*-

# Calibre Enhancements add-on for NVDA
# Calibre book viewer support
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.
#Copyright (C) 2020 Javi Dominguez <fjavids@gmail.com>

import appModuleHandler
import addonHandler
import scriptHandler
import api
import controlTypes
# controlTypes module compatibility with old versions of NVDA
if not hasattr(controlTypes, "Role"):
	setattr(controlTypes, Role, type('Enum', (), dict(
	[(x.split("ROLE_")[1], getattr(controlTypes, x)) for x in dir(controlTypes) if x.startswith("ROLE_")])))
if not hasattr(controlTypes, "State"):
	setattr(controlTypes, State, type('Enum', (), dict(
	[(x.split("STATE_")[1], getattr(controlTypes, x)) for x in dir(controlTypes) if x.startswith("STATE_")])))
# End of compatibility fixes
import ui
import winUser
from time import sleep
from speech import speakText, speakObject
from keyboardHandler import KeyboardInputGesture
from NVDAObjects.UIA import UIA

addonHandler.initTranslation()

class AppModule(appModuleHandler.AppModule):

	# TRANSLATORS: category for Calibre input gestures
	scriptCategory = _("Calibre")

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		self.alreadySpoken = []
		self.section = None
		self.currentParagraph = None
		self.lastToolbarItem = None

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if (obj.role == controlTypes.Role.LISTITEM and controlTypes.State.SELECTABLE in obj.states and obj.childCount > 0): #  or (obj.role == controlTypes.Role.STATICTEXT and obj.name and obj.container.role == controlTypes.Role.LISTITEM):
			clsList.insert(0, ToolBarButton)

	def event_foreground(self, fg, nextHandler):
		try:
			obj = fg.getChild(2).getChild(1)
		except:
			pass
		else:
			if obj.name: speakText(obj.name)
		nextHandler()

	def readPage(self, direction=None):
		fg = api.getForegroundObject()
		focus = api.getFocusObject()
		section = focus.name if focus and focus.name else None
		if section != self.section:
			obj = api.getFocusObject().parent
			self.section = section
		else:
			try:
				obj = self.getWebViewPanel().firstChild.firstChild.firstChild.getChild(2)
			except:
				speakText(_("Text not found"))
				return
		textOnScreen = filter(lambda o: o.role == controlTypes.Role.STATICTEXT and controlTypes.State.OFFSCREEN not in o.states and obj not in self.alreadySpoken, obj.recursiveDescendants)
		if textOnScreen:
			textOnScreen = list(textOnScreen)
			if textOnScreen == self.alreadySpoken:
				try:
					self.mouseClick(textOnScreen[-1])
				except IndexError:
					pass
				return	
			if direction == None:
				page = "\n".join([i.name for i in textOnScreen])
				speakText(page)
				direction = 0
			else:
				speakText(textOnScreen[direction].name)
			self.currentParagraph = textOnScreen[direction]
			api.setNavigatorObject(textOnScreen[direction])
			textOnScreen[direction].scrollIntoView
			self.alreadySpoken = textOnScreen

	def script_nextToolbarItem(self, gesture):
		if self.isToolBarOpen():
			self.gotoToolbarItem(+1)
			return
		elif api.getNavigatorObject() == self.currentParagraph:
			ui.message(_("Tool bar is hidden"))
			return
		gesture.send()

	def script_readNext(self, gesture):
		if api.getFocusObject().role in [controlTypes.Role.POPUPMENU, controlTypes.Role.MENUITEM]:
			gesture.send()
			return
		if self.isToolBarOpen():
			KeyboardInputGesture.fromName("escape").send()
			sleep(0.10)
		obj = self.currentParagraph.simpleNext if self.currentParagraph else None
		if obj and obj in self.alreadySpoken:
			speakText(obj.name)
			self.currentParagraph = obj
			api.setNavigatorObject(self.currentParagraph)
			self.currentParagraph.scrollIntoView()
		else:
			gesture.send()
			sleep(0.15)
			self.readPage(0)

	def script_previousToolbarItem(self, gesture):
		if self.isToolBarOpen():
			self.gotoToolbarItem(-1)
			return
		elif api.getNavigatorObject() == self.currentParagraph:
			ui.message(_("Tool bar is hidden"))
			return
		gesture.send()

	def script_readPrevious(self, gesture):
		if api.getFocusObject().role in [controlTypes.Role.POPUPMENU, controlTypes.Role.MENUITEM]:
			gesture.send()
			return
		if self.isToolBarOpen():
			KeyboardInputGesture.fromName("escape").send()
			sleep(0.10)
		obj = self.currentParagraph.simplePrevious if self.currentParagraph else None
		if obj and obj in self.alreadySpoken:
			speakText(obj.name)
			self.currentParagraph = obj
			api.setNavigatorObject(self.currentParagraph)
			self.currentParagraph.scrollIntoView()
		else:
			gesture.send()
			sleep(0.15)
			self.readPage(-1)

	def script_read(self, gesture):
		gesture.send()
		sleep(0.15)
		self.readPage()

	def script_toolBar(self, gesture):
		gesture.send()
		sleep(0.15)
		if self.isToolBarOpen():
			speakText(_("Tool bar"))
			self.gotoToolbarItem()

	def gotoToolbarItem(self, itemIndex=0):
		fg = api.getForegroundObject()
		try:
			toolBar = self.getWebViewPanel().firstChild.firstChild.firstChild.getChild(5)
		except:
			return
		toolBarMenu = list(filter(lambda o: o.role in [
		controlTypes.Role.BUTTON,
		controlTypes.Role.LINK,
		controlTypes.Role.EDITABLETEXT
		] and controlTypes.State.OFFSCREEN not in o.states, toolBar.recursiveDescendants))
		if itemIndex > 0 or itemIndex < 0:
			try:
				itemIndex = toolBarMenu.index(self.lastToolbarItem)+itemIndex
				if itemIndex >= len(toolBarMenu): itemIndex = 0
			except ValueError:
				menuItem=0
		item = toolBarMenu[itemIndex]
		self.lastToolbarItem = item
		api.setNavigatorObject(item)
		if item.role == controlTypes.Role.EDITABLETEXT:
			self.mouseClick(item)
		speakObject(item)

	def script_toggleToolbar(self, gesture):
		if self.isToolBarOpen():
			if self.currentParagraph:
				api.setNavigatorObject(self.currentParagraph)
				speakText(self.currentParagraph.name)
			else:
				speakText(_("Text"))
			gesture.send()
			return
		gesture.send()

	def script_enter(self, gesture):
		if self.isToolBarOpen() and api.getNavigatorObject() == self.lastToolbarItem:
			self.mouseClick(self.lastToolbarItem)
			sleep(0.1)
			obj = self.getWebViewPanel().firstChild.firstChild.firstChild.getChild(5).getChild(1).firstChild
			if obj:
				speakText(obj.name)
				# api.setNavigatorObject(obj)
				self.gotoToolbarItem()
			return
		gesture.send()

	def script_startPage(self, gesture):
		self.readPage(0)

	def mouseClick(self, obj, button="left"):
		api.moveMouseToNVDAObject(obj)
		api.setMouseObject(obj)
		if button == "left":
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
		if button == "right":
			winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN,0,0,None,None)
			winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTUP,0,0,None,None)

	def isToolBarOpen(self):
		fg = api.getForegroundObject()
		toolBar = None
		try:
			toolBar = self.getWebViewPanel().firstChild.firstChild.firstChild.getChild(5)
		except:
			pass
		if toolBar:
			return True
		else:
			return False

	def getWebViewPanel(self):
		obj = None
		fg = api.getForegroundObject()
		for child in fg.children:
			if child.UIAElement.currentClassName == "WebView":
				obj = child
				break
		return obj
		
	__gestures = {
	"kb:downArrow": "readNext",
	"kb:upArrow": "readPrevious",
	"kb:pageUp": "read",
	"kb:pageDown": "read",
	"kb:control+pageUp": "read",
	"kb:control+pageDown": "read",
	"kb:applications": "toolBar",
	"kb:escape": "toggleToolbar",
	"kb:enter": "enter",
	"kb:tab": "nextToolbarItem",
	"kb:shift+tab": "previousToolbarItem"
	}

class ToolBarButton(UIA):

	def initOverlayClass(self):
		self.role = controlTypes.Role.BUTTON
		if not self.name:
			names = []
			for o in self.recursiveDescendants:
				if o.name: names.append(o.name)
			self.name = " ".join(names)
