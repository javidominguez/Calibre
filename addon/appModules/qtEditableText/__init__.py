# -*- coding: UTF-8 -*-

# NVDA object class for editable text in QT interfaces
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.
#Copyright (C) 2018 Javi Dominguez <fjavids@gmail.com>

from NVDAObjects.behaviors import EditableTextWithAutoSelectDetection
from string import printable, punctuation
from keyboardHandler import KeyboardInputGesture
from globalCommands import commands
from locale import getdefaultlocale
import scriptHandler
import config
import ui

SpecialAlphanumeric = {
"en": printable[:62],
"es": printable[:62]+u"áéíóúàèìòùäëïöüâêîôûñçÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛÑÇ"
}

class QTEditableText(EditableTextWithAutoSelectDetection):

	def _get_language(self):
		return getdefaultlocale()[0].split("_")[0]

	def initOverlayClass(self, *args, **kwargs):
		self.debug = False
		self.fakeCaret = len(self.value)-1 if self.value else 0
		self.startSelection = -1
		self.alphanumeric = SpecialAlphanumeric[self.language] if self.language in SpecialAlphanumeric else SpecialAlphanumeric["en"]
		self.sign = ""
		for k in commands._gestureMap:
			if commands._gestureMap[k].__name__ == "script_reportCurrentSelection":
				self.bindGesture(k, "reportCurrentSelection")

	def event_gainFocus(self):
		self.reportFocus()
		self.typeBuffer = ""

	def event_typedCharacter(self, *args, **kwargs):
		self.startSelection = -1
		ch = kwargs["ch"]
		if ch in self.alphanumeric+punctuation:
			self.typeBuffer = self.typeBuffer+ch
			self.fakeCaret = self.fakeCaret+1
			if config.conf["keyboard"]["speakTypedCharacters"]: ui.message(ch)
		else:
			if self.typeBuffer:
				if config.conf["keyboard"]["speakTypedWords"]: ui.message(self.typeBuffer)
				self.typeBuffer = ""
		if ch == " ": self.fakeCaret = self.fakeCaret+1

	def event_caret(self):
		if self.debug: ui.message(str(self.fakeCaret))

	def script_nextCh(self, gesture):
		self.typeBuffer = ""
		self.startSelection = -1
		gesture.send()
		self.nextCh()

	def script_selectNextCh(self, gesture):
		self.typeBuffer = ""
		if self.startSelection < 0: self.startSelection = self.fakeCaret
		sizeBefore = self.startSelection-self.fakeCaret if self.startSelection > self.fakeCaret else self.fakeCaret-self.startSelection
		gesture.send()
		self.nextCh(1)
		sizeAfter = self.startSelection-self.fakeCaret if self.startSelection > self.fakeCaret else self.fakeCaret-self.startSelection
		if sizeAfter > sizeBefore:
			ui.message(_("selected"))
		else:
			if self.fakeCaret < len(self.value): ui.message(_("deselected"))

	def nextCh(self, selection=0):
		if self.value:
			if self.fakeCaret < len(self.value): self.fakeCaret = self.fakeCaret+1
			try:
				if self.fakeCaret < len(self.value)+1: ui.message(self.value[self.fakeCaret-selection])
			except IndexError:
				pass

	def script_previousCh(self, gesture):
		self.typeBuffer = ""
		self.startSelection = -1
		gesture.send()
		self.previousCh()

	def script_selectPreviousCh(self, gesture):
		self.typeBuffer = ""
		if self.startSelection < 0: self.startSelection = self.fakeCaret
		sizeBefore = self.startSelection-self.fakeCaret if self.startSelection > self.fakeCaret else self.fakeCaret-self.startSelection
		gesture.send()
		self.previousCh(1)
		sizeAfter = self.startSelection-self.fakeCaret if self.startSelection > self.fakeCaret else self.fakeCaret-self.startSelection
		if sizeAfter > sizeBefore:
			ui.message(_("selected"))
		else:
			if self.fakeCaret > 0: ui.message(_("deselected"))

	def previousCh(self, selection=0):
		if self.value:
			if self.fakeCaret > 0: self.fakeCaret = self.fakeCaret-1
			if selection and self.fakeCaret == 0: ui.message(self.value[self.fakeCaret])
			else:
				ui.message(self.value[self.fakeCaret])

	def script_end(self, gesture):
		self.typeBuffer = ""
		self.startSelection = -1
		gesture.send()
		if self.value:
			self.fakeCaret = len(self.value)
			if self.fakeCaret < len(self.value): ui.message(self.value[self.fakeCaret ])

	def script_selectEnd(self, gesture):
		self.typeBuffer = ""
		if self.startSelection < 0:
			self.startSelection = self.fakeCaret
			unselection = False
		else:
			unselection = True
		gesture.send()
		if self.value:
			self.fakeCaret = len(self.value)
			if not unselection or self.fakeCaret > self.startSelection:
				ui.message(self.value[self.startSelection:])
				ui.message(_("selected"))
			else:
				ui.message(_("deselected"))

	def script_home(self, gesture):
		self.typeBuffer = ""
		self.startSelection = -1
		gesture.send()
		if self.fakeCaret > 0: self.fakeCaret = 0
		if self.value: ui.message(self.value[self.fakeCaret ])

	def script_selectHome(self, gesture):
		self.typeBuffer = ""
		if self.startSelection < 0:
			self.startSelection = self.fakeCaret
			unselection = False
		else:
			unselection = True
		gesture.send()
		self.fakeCaret = 0
		if self.value:
			ui.message(self.value[self.fakeCaret:self.startSelection])
			if not unselection or self.fakeCaret < self.startSelection:
				ui.message(_("selected"))
			else:
				ui.message(_("deselected"))

	def script_supr(self, gesture):
		self.typeBuffer = ""
		value = self.value
		gesture.send()
		if self.startSelection >= 0:
			self.removeSelection(value)
			return
		try:
			if self.value: ui.message(self.value[self.fakeCaret+1])
		except IndexError:
			pass

	def script_back(self, gesture):
		self.typeBuffer = ""
		if self.startSelection >= 0:
			value = self.value
			gesture.send()
			self.removeSelection(value)
			return
		if self.value and self.fakeCaret > 0: ui.message(self.value[self.fakeCaret-1])
		gesture.send()
		if self.fakeCaret > 0: self.fakeCaret = self.fakeCaret - 1

	def script_removeWords(self, gesture):
		self.typeBuffer = ""
		if self.startSelection >= self.fakeCaret:
			value = self.value
			if gesture.mainKeyName == "backspace":
				self.previousWord()
				ui.message(_("selected"))
			else:
				self.nextWord(1)
				ui.message(_("deselected"))
			gesture.send()
			self.removeSelection(value)
			return
		elif self.startSelection >= 0:
			if gesture.mainKeyName == "backspace":
				self.previousWord()
				ui.message(_("deselected"))
			else:
				self.nextWord(1)
				ui.message(_("selected"))
			value = self.value
			gesture.send()
			self.removeSelection(value)
			return
		if gesture.mainKeyName == "backspace":
			self.previousWord()
			gesture.send()
			ui.message(_("selection removed"))
		elif gesture.mainKeyName == "delete":
			oldCaret = self.fakeCaret
			self.nextWord(1)
			gesture.send()
			ui.message(_("selection removed"))
			self.fakeCaret = oldCaret


	def script_cut(self, gesture):
		value = self.value
		gesture.send()
		self.removeSelection(value)

	def removeSelection(self, value=""):
		if self.startSelection <0 or self.fakeCaret == self.startSelection or not value: return
		if self.startSelection > self.fakeCaret:
			ui.message(value[self.fakeCaret:self.startSelection])
		else:
			ui.message(value[self.startSelection:self.fakeCaret])
			self.fakeCaret = self.startSelection
		ui.message(_("selection removed"))
		self.startSelection = -1

	def script_nextWord(self, gesture):
		self.typeBuffer = ""
		self.startSelection = -1
		gesture.send()
		self.nextWord()

	def script_selectNextWord(self, gesture):
		self.typeBuffer = ""
		if self.startSelection < 0: self.startSelection = self.fakeCaret
		sizeBefore = self.startSelection-self.fakeCaret if self.startSelection > self.fakeCaret else self.fakeCaret-self.startSelection
		gesture.send()
		self.nextWord(1)
		sizeAfter = self.startSelection-self.fakeCaret if self.startSelection > self.fakeCaret else self.fakeCaret-self.startSelection
		if sizeAfter>sizeBefore:
			ui.message(_("selected"))
		else:
			if self.fakeCaret < len(self.value): ui.message(_("deselected"))

	def nextWord(self, selection=0):
		if self.value:
			oldCaret = self.fakeCaret
			if self.fakeCaret >= len(self.value): return
			if self.value[self.fakeCaret] in punctuation:
				try:
					while self.value[self.fakeCaret] in punctuation:
						self.fakeCaret = self.fakeCaret+1
				except IndexError:
					return
				try:
					while self.value[self.fakeCaret] == " ":
						self.fakeCaret = self.fakeCaret+1
				except IndexError:
					return
			else:
				try:
					while self.value[self.fakeCaret] in self.alphanumeric:
						self.fakeCaret = self.fakeCaret+1
				except IndexError:
					if selection:
						ui.message("%s%s" % (self.value[oldCaret:self.fakeCaret-1], self.value[self.fakeCaret-1]))
					return
				try:
					while self.value[self.fakeCaret] == " ":
						self.fakeCaret = self.fakeCaret+1
				except IndexError:
					if selection:
						ui.message("%s%s" % (self.value[oldCaret:self.fakeCaret-1], self.value[self.fakeCaret-1]))
					return
			try:
				if selection:
					ui.message(self.value[oldCaret:self.fakeCaret])
				else:
					ui.message(self.value[self.fakeCaret:].split()[0])
			except IndexError:
				pass

	def script_previousWord(self, gesture):
		self.typeBuffer = ""
		self.startSelection = -1
		gesture.send()
		self.previousWord()

	def script_selectPreviousWord(self, gesture):
		self.typeBuffer = ""
		if self.startSelection < 0: self.startSelection = self.fakeCaret
		sizeBefore = self.startSelection-self.fakeCaret if self.startSelection > self.fakeCaret else self.fakeCaret-self.startSelection
		gesture.send()
		self.previousWord(True)
		sizeAfter = self.startSelection-self.fakeCaret if self.startSelection > self.fakeCaret else self.fakeCaret-self.startSelection
		if sizeAfter > sizeBefore:
			ui.message(_("selected"))
		else:
			if self.fakeCaret > 0: ui.message(_("deselected"))

	def previousWord(self, selection=False):
		if self.value:
			if self.fakeCaret < 1:
				return
			if self.fakeCaret >= len(self.value):
				self.fakeCaret = self.fakeCaret-1
			oldCaret = self.fakeCaret
			# Current character is a punctuation mark
			if self.fakeCaret >0 and self.value[self.fakeCaret] in punctuation and self.value[self.fakeCaret-1] not in punctuation:
				self.fakeCaret = self.fakeCaret-1
			if self.value[self.fakeCaret] in punctuation and self.fakeCaret >= 0:
				while self.value[self.fakeCaret] in punctuation and self.fakeCaret >= 0:
					self.fakeCaret = self.fakeCaret-1
				self.fakeCaret = self.fakeCaret+1
				if selection:
					ui.message(self.value[self.fakeCaret:oldCaret])
				else:
					ui.message(self.value[self.fakeCaret])
				return
			# Current character is an space
			if self.value[self.fakeCaret] == " " and self.fakeCaret > 0:
				while self.value[self.fakeCaret] == " " and self.fakeCaret > 0:
					self.fakeCaret = self.fakeCaret-1
				group = self.alphanumeric if self.value[self.fakeCaret] in self.alphanumeric else punctuation
				self.fakeCaret = self.fakeCaret-1 if self.fakeCaret > 0 else 0
				while self.value[self.fakeCaret] in group and self.fakeCaret >0:
					self.fakeCaret = self.fakeCaret-1
				if self.fakeCaret > 0:
					self.fakeCaret = self.fakeCaret+1
				ui.message(self.value[self.fakeCaret:oldCaret])
				return
			# Current character is alphanumeric
			if self.fakeCaret > 0 and self.value[self.fakeCaret-1] in self.alphanumeric+" ":
				self.fakeCaret = self.fakeCaret-1
			if self.value[self.fakeCaret] in self.alphanumeric and self.fakeCaret > 0:
				while self.value[self.fakeCaret] in self.alphanumeric and self.fakeCaret > 0:
					self.fakeCaret = self.fakeCaret-1
				if self.fakeCaret>0:
					self.fakeCaret = self.fakeCaret+1
				#@ ui.message(str(oldCaret))
				if oldCaret == len(self.value)-1:
					oldCaret = oldCaret+1
				ui.message(self.value[self.fakeCaret:oldCaret])
				return
			else:
				group = punctuation if self.value[self.fakeCaret] in punctuation else " "
				while self.value[self.fakeCaret] in group and self.fakeCaret > 0:
					self.fakeCaret = self.fakeCaret-1
				if self.value[self.fakeCaret+1] == " ":
					group = punctuation if self.value[self.fakeCaret] in punctuation else self.alphanumeric
					while self.value[self.fakeCaret] in group and self.fakeCaret > 0:
						self.fakeCaret = self.fakeCaret-1
				if self.fakeCaret > 0:
					self.fakeCaret = self.fakeCaret+1
			ui.message(self.value[self.fakeCaret:oldCaret])

	def script_reportCurrentSelection(self, gesture):
		if self.startSelection <0 or self.fakeCaret == self.startSelection or not self.value:
			scriptHandler.executeScript(commands.script_reportCurrentSelection, None)
			return
		ui.message(_("selected"))
		if self.startSelection > self.fakeCaret:
			ui.message(self.value[self.fakeCaret:self.startSelection])
		else:
			ui.message(self.value[self.startSelection:self.fakeCaret])
	script_reportCurrentSelection.__doc__ = commands.script_reportCurrentSelection.__doc__

	__gestures = {
	"kb:rightArrow":"nextCh",
	"kb:shift+rightArrow":"selectNextCh",
	"kb:leftArrow":"previousCh",
	"kb:shift+leftArrow":"selectPreviousCh",
	"kb:end":"end",
	"kb:shift+end":"selectEnd",
	"kb:home":"home",
	"kb:shift+home":"selectHome",
	"kb:delete":"supr",
	"kb:backspace":"back",
	"kb:control+backspace":"removeWords",
	"kb:control+delete":"removeWords",
	"kb:control+rightArrow":"nextWord",
	"kb:control+shift+rightArrow":"selectNextWord",
	"kb:control+leftArrow":"previousWord",
	"kb:control+shift+leftArrow":"selectPreviousWord"
	}

