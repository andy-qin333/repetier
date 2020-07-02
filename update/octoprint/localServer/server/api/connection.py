# coding=utf-8

__author__ = "Gina Häußge <osd@foosel.net>"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
__copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"



from octoprint.settings import settings
from octoprint.printer import get_connection_options
from octoprint.server import printer, printerProfileManager

import api_util as util
from api_util import make_response,NO_CONTENT,get_json_command_from_request



def connectionState():
	state, port, baudrate, printer_profile = printer.get_current_connection()
	current = {
		"state": state,
		"port": port,
		"baudrate": baudrate,
		"printerProfile": printer_profile["id"] if printer_profile is not None and "id" in printer_profile else "_default"
	}

	return jsonify({"current": current, "options": _get_options()})



def connectionCommand(request=None):
	valid_commands = {
		"connect": [],
		"disconnect": [],
		"fake_ack": []
	}

	command, data, response = get_json_command_from_request(request, valid_commands)
	if response is not None:
		return response

	if command == "connect":
		connection_options = get_connection_options()

		port = None
		baudrate = None
		printerProfile = None
		if "port" in data.keys():
			port = data["port"]
			if port not in connection_options["ports"] and port != "AUTO":
				return make_response("Invalid port: %s" % port, 400)
		if "baudrate" in data.keys():
			baudrate = data["baudrate"]
			if baudrate not in connection_options["baudrates"] and baudrate != 0:
				return make_response("Invalid baudrate: %d" % baudrate, 400)
		if "printerProfile" in data.keys():
			printerProfile = data["printerProfile"]
			if not printerProfileManager.exists(printerProfile):
				return make_response("Invalid printer profile: %s" % printerProfile, 400)
		if "save" in data.keys() and data["save"]:
			settings().set(["serial", "port"], port)
			settings().setInt(["serial", "baudrate"], baudrate)
			printerProfileManager.set_default(printerProfile)
		if "autoconnect" in data.keys():
			settings().setBoolean(["serial", "autoconnect"], data["autoconnect"])
		settings().save()
		printer.connect(port=port, baudrate=baudrate, profile=printerProfile)
	elif command == "disconnect":
		printer.disconnect()
	elif command == "fake_ack":
		printer.fake_ack()

	return NO_CONTENT

def _get_options():
	connection_options = get_connection_options()
	profile_options = printerProfileManager.get_all()
	default_profile = printerProfileManager.get_default()

	options = dict(
		ports=connection_options["ports"],
		baudrates=connection_options["baudrates"],
		printerProfiles=[dict(id=printer_profile["id"], name=printer_profile["name"] if "name" in printer_profile else printer_profile["id"]) for printer_profile in profile_options.values() if "id" in printer_profile],
		portPreference=connection_options["portPreference"],
		baudratePreference=connection_options["baudratePreference"],
		printerProfilePreference=default_profile["id"] if "id" in default_profile else None
	)

	return options