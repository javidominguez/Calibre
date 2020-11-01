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
import ui
import winUser
from time import sleep
from speech import speakText
from keyboardHandler import KeyboardInputGesture

addonHandler.initTranslation()

class AppModule(appModuleHandler.AppModule):

	# TRANSLATORS: category for Calibre input gestures
	scriptCategory = _("Calibre")

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		self.alreadySpoken = []
		self.section = None
		self.currentParagraph = None
		self.lastMenuItem = None

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
		textOnScreen = filter(lambda o: o.role == controlTypes.ROLE_STATICTEXT and controlTypes.STATE_OFFSCREEN not in o.states and obj not in self.alreadySpoken, obj.recursiveDescendants)
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

	def script_readNext(self, gesture):
		if api.getFocusObject().role in [controlTypes.ROLE_POPUPMENU, controlTypes.ROLE_MENUITEM]:
			gesture.send()
			return
		if self.isToolBarOpen():
			self.gotoMenuItem(+1)
			return
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

	def script_readPrevious(self, gesture):
		if api.getFocusObject().role in [controlTypes.ROLE_POPUPMENU, controlTypes.ROLE_MENUITEM]:
			gesture.send()
			return
		if self.isToolBarOpen():
			self.gotoMenuItem(-1)
			return
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
			speakText(_("menu"))
			self.gotoMenuItem()

	def gotoMenuItem(self, itemIndex=0):
		fg = api.getForegroundObject()
		toolBar = self.getWebViewPanel().firstChild.firstChild.firstChild.getChild(5)
		toolBarMenu = list(filter(lambda o: o.role == controlTypes.ROLE_STATICTEXT and o.name and o.parent.role == controlTypes.ROLE_LISTITEM and controlTypes.STATE_OFFSCREEN not in o.states, toolBar.recursiveDescendants))
		if itemIndex > 0 or itemIndex < 0:
			try:
				itemIndex = toolBarMenu.index(self.lastMenuItem)+itemIndex
				if itemIndex >= len(toolBarMenu): itemIndex = 0
			except ValueError:
				menuItem=0
		item = toolBarMenu[itemIndex]
		self.lastMenuItem = item
		api.setNavigatorObject(item)
		if item.parent.name:
			speakText(item.parent.name)
		else:
			speakText(item.name)

	def script_toggleMenu(self, gesture):
		if self.isToolBarOpen():
			if self.currentParagraph:
				api.setNavigatorObject(self.currentParagraph)
				speakText(self.currentParagraph.name)
			else:
				speakText(_("Text"))
			gesture.send()
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
	"kb:escape": "toggleMenu"
	}