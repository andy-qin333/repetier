# coding=utf-8

__author__ = "Gina Häußge <osd@foosel.net>, Lars Norpchen"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
__copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"

import datetime
import logging
import subprocess
import Queue
import threading
import collections

from octoprint.settings import settings
#import octoprint.plugin

# singleton
_instance = None

def eventManager():
	global _instance
	if _instance is None:
		_instance = EventManager()
	return _instance


class EventManager(object):
	"""
	Handles receiving events and dispatching them to subscribers
	"""

	def __init__(self):
		self._registeredListeners = collections.defaultdict(list)
		self._logger = logging.getLogger(__name__)

		self._queue = Queue.Queue()
		self._worker = threading.Thread(target=self._work)
		self._worker.daemon = True
		self._worker.start()

	def _work(self):
		try:
			while True:
				event, payload = self._queue.get(True)

				eventListeners = self._registeredListeners[event]
				self._logger.debug("Firing event: %s (Payload: %r)" % (event, payload))

				for listener in eventListeners:
					self._logger.debug("Sending action to %r" % listener)
					try:
						listener(event, payload)
					except:
						self._logger.exception("Got an exception while sending event %s (Payload: %r) to %s" % (event, payload, listener))

				#octoprint.plugin.call_plugin(octoprint.plugin.types.EventHandlerPlugin,
				                             #"on_event",
				                             #args=[event, payload])
		except:
			self._logger.exception("Ooops, the event bus worker loop crashed")

	def fire(self, event, payload=None):
		"""
		Fire an event to anyone subscribed to it

		Any object can generate an event and any object can subscribe to the event's name as a string (arbitrary, but
		case sensitive) and any extra payload data that may pertain to the event.

		Callbacks must implement the signature "callback(event, payload)", with "event" being the event's name and
		payload being a payload object specific to the event.
		"""

		self._queue.put((event, payload))

	def subscribe(self, event, callback):
		"""
		Subscribe a listener to an event -- pass in the event name (as a string) and the callback object
		"""

		if callback in self._registeredListeners[event]:
			# callback is already subscribed to the event
			return

		self._registeredListeners[event].append(callback)
		self._logger.debug("Subscribed listener %r for event %s" % (callback, event))

	def unsubscribe (self, event, callback):
		"""
		Unsubscribe a listener from an event -- pass in the event name (as string) and the callback object
		"""

		if not callback in self._registeredListeners[event]:
			# callback not subscribed to event, just return
			return

		self._registeredListeners[event].remove(callback)
		self._logger.debug("Unsubscribed listener %r for event %s" % (callback, event))


class GenericEventListener(object):
	"""
	The GenericEventListener can be subclassed to easily create custom event listeners.
	"""

	def __init__(self):
		self._logger = logging.getLogger(__name__)

	def subscribe(self, events):
		"""
		Subscribes the eventCallback method for all events in the given list.
		"""

		for event in events:
			eventManager().subscribe(event, self.eventCallback)

	def unsubscribe(self, events):
		"""
		Unsubscribes the eventCallback method for all events in the given list
		"""

		for event in events:
			eventManager().unsubscribe(event, self.eventCallback)

	def eventCallback(self, event, payload):
		"""
		Actual event callback called with name of event and optional payload. Not implemented here, override in
		child classes.
		"""
		pass


class CommandTrigger(GenericEventListener):
	def __init__(self, action):
		GenericEventListener.__init__(self)
		self._action = action
		self._subscriptions = {}

		self._initSubscriptions()

	def _initSubscriptions(self):
		"""
		Subscribes all events as defined in "events > $triggerType > subscriptions" in the settings with their
		respective commands.
		"""

		eventsToSubscribe = []
		
		for event in self._action.getMethodsMap():

			if not event in self._subscriptions.keys():
				self._subscriptions[event] = []
			self._subscriptions[event].append(self._action.getMethodsMap()[event])

			if not event in eventsToSubscribe:
				eventsToSubscribe.append(event)

		self.subscribe(eventsToSubscribe)

	def eventCallback(self, event, payload):
		"""
		Event callback, iterates over all subscribed commands for the given event, processes the command
		string and then executes the command via the abstract executeCommand method.
		"""

		GenericEventListener.eventCallback(self, event, payload)

		if not event in self._subscriptions:
			return

		for callback in self._subscriptions[event]:
			try:
				if isinstance(callback, (tuple, list, set)):
					for c in callback:
						c(payload)
				else:
					callback(payload)
			except KeyError, e:
				self._logger.warn("There was an error processing one or more placeholders in the following callback: %s" % callback)
