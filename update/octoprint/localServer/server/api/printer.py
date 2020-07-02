# coding=utf-8

__author__ = "Gina Häußge <osd@foosel.net>"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
__copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"

import re

from octoprint.settings import settings, valid_boolean_trues
from octoprint.server import printer, printerProfileManager
from octoprint.printer import UnknownScript

from api_util import make_response,NO_CONTENT,get_json_command_from_request

#~~ Printer


#~~ Tool

def printerToolCommand(request=None):
	if not printer.is_operational():
		return make_response("Printer is not operational", 409)

	valid_commands = {
		"select": ["tool"],
		"target": ["targets"],
		"offset": ["offsets"],
		"extrude": ["amount"],
		"flowrate": ["factor"]
	}
	command, data, response = get_json_command_from_request(request, valid_commands)
	if response is not None:
		return response

	validation_regex = re.compile("(tool\d+)|(chamber)")

	##~~ tool selection
	if command == "select":
		tool = data["tool"]
		if re.match(validation_regex, tool) is None:
			return make_response("Invalid tool: %s" % tool, 400)
		if not tool.startswith("tool"):
			return make_response("Invalid tool for selection: %s" % tool, 400)

		printer.change_tool(tool)

	##~~ temperature
	elif command == "target":
		targets = data["targets"]

		# make sure the targets are valid and the values are numbers
		validated_values = {}
		for tool, value in targets.iteritems():
			if re.match(validation_regex, tool) is None:
				return make_response("Invalid target for setting temperature: %s" % tool, 400)
			if not isinstance(value, (int, long, float)):
				return make_response("Not a number for %s: %r" % (tool, value), 400)
			validated_values[tool] = value

		# perform the actual temperature commands
		for tool in validated_values.keys():
			printer.set_temperature(tool, validated_values[tool])

	##~~ temperature offset
	elif command == "offset":
		offsets = data["offsets"]

		# make sure the targets are valid, the values are numbers and in the range [-50, 50]
		validated_values = {}
		for tool, value in offsets.iteritems():
			if re.match(validation_regex, tool) is None:
				return make_response("Invalid target for setting temperature: %s" % tool, 400)
			if not isinstance(value, (int, long, float)):
				return make_response("Not a number for %s: %r" % (tool, value), 400)
			if not -50 <= value <= 50:
				return make_response("Offset %s not in range [-50, 50]: %f" % (tool, value), 400)
			validated_values[tool] = value

		# set the offsets
		printer.set_temperature_offset(validated_values)

	##~~ extrusion
	elif command == "extrude":
		if printer.is_printing():
			# do not extrude when a print job is running
			return make_response("Printer is currently printing", 409)

		amount = data["amount"]
		if not isinstance(amount, (int, long, float)):
			return make_response("Not a number for extrusion amount: %r" % amount, 400)
		printer.extrude(amount)

	elif command == "flowrate":
		factor = data["factor"]
		if not isinstance(factor, (int, long, float)):
			return make_response("Not a number for flow rate: %r" % factor, 400)
		try:
			printer.flow_rate(factor)
		except ValueError as e:
			return make_response("Invalid value for flow rate: %s" % str(e), 400)

	return NO_CONTENT

def printerToolState():
	if not printer.is_operational():
		return make_response("Printer is not operational", 409)

	#return jsonify(_get_temperature_data(_delete_bed))
	return jsonify(_get_temperature_data(_delete_bed_and_chamber)) # zyd for add chamber


##~~ Heated bed

def printerBedCommand(request=None):
	if not printer.is_operational():
		return make_response("Printer is not operational", 409)

	if not printerProfileManager.get_current_or_default()["heatedBed"]:
		return make_response("Printer does not have a heated bed", 409)

	valid_commands = {
		"target": ["target"],
		"offset": ["offset"]
	}
	command, data, response = get_json_command_from_request(request, valid_commands)
	if response is not None:
		return response

	##~~ temperature
	if command == "target":
		target = data["target"]

		# make sure the target is a number
		if not isinstance(target, (int, long, float)):
			return make_response("Not a number: %r" % target, 400)

		# perform the actual temperature command
		printer.set_temperature("bed", target)

	##~~ temperature offset
	elif command == "offset":
		offset = data["offset"]

		# make sure the offset is valid
		if not isinstance(offset, (int, long, float)):
			return make_response("Not a number: %r" % offset, 400)
		if not -50 <= offset <= 50:
			return make_response("Offset not in range [-50, 50]: %f" % offset, 400)

		# set the offsets
		printer.set_temperature_offset({"bed": offset})

	return NO_CONTENT


def printerBedState():
	if not printer.is_operational():
		return make_response("Printer is not operational", 409)

	if not printerProfileManager.get_current_or_default()["heatedBed"]:
		return make_response("Printer does not have a heated bed", 409)

	#data = _get_temperature_data(_delete_tools)
	data = _get_temperature_data(_delete_tools_and_chamber) # zyd for add chamber
	if isinstance(data, Response):
		return data
	else:
		return jsonify(data)


# zyd for add chamber -s
##~~ Heated chamber
def printerChamberCommand():
	if not printer.is_operational():
		return make_response("Printer is not operational", 409)

	if not printerProfileManager.get_current_or_default()["heatedChamber"]:
		return make_response("Printer does not have a heated chamber", 409)

	valid_commands = {
		"target": ["target"],
		"offset": ["offset"]
	}
	command, data, response = get_json_command_from_request(request, valid_commands)
	if response is not None:
		return response

	##~~ temperature
	if command == "target":
		target = data["target"]

		# make sure the target is a number
		if not isinstance(target, (int, long, float)):
			return make_response("Not a number: %r" % target, 400)

		# perform the actual temperature command
		printer.set_temperature("chamber", target)

	##~~ temperature offset
	elif command == "offset":
		offset = data["offset"]

		# make sure the offset is valid
		if not isinstance(offset, (int, long, float)):
			return make_response("Not a number: %r" % offset, 400)
		if not -50 <= offset <= 50:
			return make_response("Offset not in range [-50, 50]: %f" % offset, 400)

		# set the offsets
		printer.set_temperature_offset({"chamber": offset})

	return NO_CONTENT


def printerChamberState():
	if not printer.is_operational():
		return make_response("Printer is not operational", 409)

	if not printerProfileManager.get_current_or_default()["heatedChamber"]:
		return make_response("Printer does not have a heated chamber", 409)

	data = _get_temperature_data(_delete_tools_and_bed) # zyd for add chamber
	if isinstance(data, Response):
		return data
	else:
		return jsonify(data)
# zyd for add chamber -e


##~~ Print head


def printerPrintheadCommand(request=None):
	valid_commands = {
		"jog": [],
	    "jogInverted": [],
		"home": ["axes"],
		"feedrate": ["factor"]
	}
	command, data, response = get_json_command_from_request(request, valid_commands)
	if response is not None:
		return response

	if not printer.is_operational() or (printer.is_printing() and command != "feedrate"):
		# do not jog when a print job is running or we don't have a connection
		return make_response("Printer is not operational or currently printing", 409)

	valid_axes = ["x", "y", "z"]
	##~~ jog command
	if command == "jog":
		# validate all jog instructions, make sure that the values are numbers
		validated_values = {}
		for axis in valid_axes:
			if axis in data:
				value = data[axis]
				if not isinstance(value, (int, long, float)):
					return make_response("Not a number for axis %s: %r" % (axis, value), 400)
				validated_values[axis] = value

		# execute the jog commands
		for axis, value in validated_values.iteritems():
			printer.jog(axis, value)
	if command == "jogInverted":
		# validate all jog instructions, make sure that the values are numbers
		validated_values = {}
		for axis in valid_axes:
			if axis in data:
				value = data[axis]
				if not isinstance(value, (int, long, float)):
					return make_response("Not a number for axis %s: %r" % (axis, value), 400)
				validated_values[axis] = value

		# execute the jog commands
		for axis, value in validated_values.iteritems():
			printer.jogInverted(axis, value)	##~~ home command
			
	elif command == "home":
		validated_values = []
		axes = data["axes"]
		for axis in axes:
			if not axis in valid_axes:
				return make_response("Invalid axis: %s" % axis, 400)
			validated_values.append(axis)

		# execute the home command
		printer.home(validated_values)

	elif command == "feedrate":
		factor = data["factor"]
		if not isinstance(factor, (int, long, float)):
			return make_response("Not a number for feed rate: %r" % factor, 400)
		try:
			printer.feed_rate(factor)
		except ValueError as e:
			return make_response("Invalid value for feed rate: %s" % str(e), 400)

	return NO_CONTENT


##~~ Commands

def printerCommand(data=None):
	if not printer.is_operational():
		return make_response("Printer is not operational", 409)
	if data is None:
		return make_response("Expected content type JSON", 400)

	if "command" in data and "commands" in data:
		return make_response("'command' and 'commands' are mutually exclusive", 400)
	elif ("command" in data or "commands" in data) and "script" in data:
		return make_response("'command'/'commands' and 'script' are mutually exclusive", 400)
	elif not ("command" in data or "commands" in data or "script" in data):
		return make_response("Need one of 'command', 'commands' or 'script'", 400)

	parameters = dict()
	if "parameters" in data:
		parameters = data["parameters"]

	if "command" in data or "commands" in data:
		if "command" in data:
			commands = [data["command"]]
		else:
			if not isinstance(data["commands"], (list, tuple)):
				return make_response("'commands' needs to be a list", 400)
			commands = data["commands"]

		commandsToSend = []
		for command in commands:
			commandToSend = command
			if len(parameters) > 0:
				commandToSend = command % parameters
			commandsToSend.append(commandToSend)

		printer.commands(commandsToSend)

	elif "script" in data:
		script_name = data["script"]
		context = dict(parameters=parameters)
		if "context" in data:
			context["context"] = data["context"]

		try:
			printer.script(script_name, context=context)
		except UnknownScript:
			return make_response("Unknown script: {script_name}".format(**locals()), 404)

	return NO_CONTENT

def getCustomControls():
	# TODO: document me
	customControls = settings().get(["controls"])
	return jsonify(controls=customControls)


def _get_temperature_data(preprocessor):
	if not printer.is_operational():
		return make_response("Printer is not operational", 409)

	tempData = printer.get_current_temperatures()

	if "history" in request.values.keys() and request.values["history"] in valid_boolean_trues:
		tempHistory = printer.get_temperature_history()

		limit = 300
		if "limit" in request.values.keys() and unicode(request.values["limit"]).isnumeric():
			limit = int(request.values["limit"])

		history = list(tempHistory)
		limit = min(limit, len(history))

		tempData.update({
			"history": map(lambda x: preprocessor(x), history[-limit:])
		})

	return preprocessor(tempData)


def _delete_tools(x):
	return _delete_from_data(x, lambda k: k.startswith("tool"))


def _delete_bed(x):
	return _delete_from_data(x, lambda k: k == "bed")

# zyd for add chamber -s
def _delete_chamber(x):
	return _delete_from_data(x, lambda k: k == "chamber")

def _delete_tools_and_bed(x):
	return _delete_from_data(x, lambda k: k.startswith("tool") or k == "bed")

def _delete_tools_and_chamber(x):
	return _delete_from_data(x, lambda k: k.startswith("tool") or k == "chamber")

def _delete_bed_and_chamber(x):
	return _delete_from_data(x, lambda k: k == "bed" or k == "chamber")
# zyd for add chamber -e


def _delete_from_data(x, key_matcher):
	data = dict(x)
	for k in data.keys():
		if key_matcher(k):
			del data[k]
	return data
