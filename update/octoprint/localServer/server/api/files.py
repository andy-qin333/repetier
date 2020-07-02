# coding=utf-8

__author__ = "Gina Häußge <osd@foosel.net>"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
__copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"


from octoprint.filemanager.destinations import FileDestinations
from octoprint.settings import settings, valid_boolean_trues
from octoprint.server import printer, fileManager, slicingManager, eventManager
from octoprint.events import Events
import octoprint.filemanager
import octoprint.slicing

from api_util import make_response,NO_CONTENT,get_json_command_from_request


#~~ GCODE file handling

def _verifyFileExists(origin, filename):
	if origin == FileDestinations.SDCARD:
		return filename in map(lambda x: x[0], printer.get_sd_files())
	else:
		return fileManager.file_exists(origin, filename)


def gcodeFileCommand(filename=None, target=None, request=None):
	if not target in [FileDestinations.LOCAL, FileDestinations.SDCARD]:
		return make_response("Unknown target: %s" % target, 404)

	if not _verifyFileExists(target, filename):
		return make_response("File not found on '%s': %s" % (target, filename), 404)

	# valid file commands, dict mapping command name to mandatory parameters
	valid_commands = {
		"select": [],
		"slice": []
	}

	command, data, response = get_json_command_from_request(request, valid_commands)
	if response is not None:
		return response

	if command == "select":
		# selects/loads a file
		printAfterLoading = False
		if "print" in data.keys() and data["print"] in valid_boolean_trues:
			if not printer.is_operational():
				return make_response("Printer is not operational, cannot directly start printing", 409)
			printAfterLoading = True
			
		# zyd for continue print when print job aborted -s
		recoverPrint = False
		if "recover" in data.keys() and data["recover"] in valid_boolean_trues:
			recoverPrint = True
		# zyd for continue print when print job aborted -e

		sd = False
		if target == FileDestinations.SDCARD:
			filenameToSelect = filename
			sd = True
		else:
			filenameToSelect = fileManager.path_on_disk(target, filename)
		printer.select_file(filenameToSelect, sd, printAfterLoading, recoverPrint)

	elif command == "slice":
		try:
			if "slicer" in data:
				slicer = data["slicer"]
				del data["slicer"]
				slicer_instance = slicingManager.get_slicer(slicer)

			elif "cura" in slicingManager.registered_slicers:
				slicer = "cura"
				slicer_instance = slicingManager.get_slicer("cura")

			else:
				return make_response("Cannot slice {filename}, no slicer available".format(**locals()), 415)
		except octoprint.slicing.UnknownSlicer as e:
			return make_response("Slicer {slicer} is not available".format(slicer=e.slicer), 400)

		if not octoprint.filemanager.valid_file_type(filename, type="stl"):
			return make_response("Cannot slice {filename}, not an STL file".format(**locals()), 415)

		if slicer_instance.get_slicer_properties()["same_device"] and (printer.is_printing() or printer.is_paused()):
			# slicer runs on same device as OctoPrint, slicing while printing is hence disabled
			return make_response("Cannot slice on {slicer} while printing due to performance reasons".format(**locals()), 409)

		if "gcode" in data and data["gcode"]:
			gcode_name = data["gcode"]
			del data["gcode"]
		else:
			import os
			name, _ = os.path.splitext(filename)
			gcode_name = name + ".gco"

		# prohibit overwriting the file that is currently being printed
		currentOrigin, currentFilename = _getCurrentFile()
		if currentFilename == gcode_name and currentOrigin == target and (printer.is_printing() or printer.is_paused()):
			make_response("Trying to slice into file that is currently being printed: %s" % gcode_name, 409)

		if "profile" in data.keys() and data["profile"]:
			profile = data["profile"]
			del data["profile"]
		else:
			profile = None

		if "printerProfile" in data.keys() and data["printerProfile"]:
			printerProfile = data["printerProfile"]
			del data["printerProfile"]
		else:
			printerProfile = None

		if "position" in data.keys() and data["position"] and isinstance(data["position"], dict) and "x" in data["position"] and "y" in data["position"]:
			position = data["position"]
			del data["position"]
		else:
			position = None

		select_after_slicing = False
		if "select" in data.keys() and data["select"] in valid_boolean_trues:
			if not printer.is_operational():
				return make_response("Printer is not operational, cannot directly select for printing", 409)
			select_after_slicing = True

		print_after_slicing = False
		if "print" in data.keys() and data["print"] in valid_boolean_trues:
			if not printer.is_operational():
				return make_response("Printer is not operational, cannot directly start printing", 409)
			select_after_slicing = print_after_slicing = True

		override_keys = [k for k in data if k.startswith("profile.") and data[k] is not None]
		overrides = dict()
		for key in override_keys:
			overrides[key[len("profile."):]] = data[key]

		def slicing_done(target, gcode_name, select_after_slicing, print_after_slicing):
			if select_after_slicing or print_after_slicing:
				sd = False
				if target == FileDestinations.SDCARD:
					filenameToSelect = gcode_name
					sd = True
				else:
					filenameToSelect = fileManager.path_on_disk(target, gcode_name)
				printer.select_file(filenameToSelect, sd, print_after_slicing)

		try:
			fileManager.slice(slicer, target, filename, target, gcode_name,
			                  profile=profile,
			                  printer_profile_id=printerProfile,
			                  position=position,
			                  overrides=overrides,
			                  callback=slicing_done,
			                  callback_args=(target, gcode_name, select_after_slicing, print_after_slicing))
		except octoprint.slicing.UnknownProfile:
			return make_response("Profile {profile} doesn't exist".format(**locals()), 400)


	return NO_CONTENT

def deleteGcodeFile(filename=None, target=None):
	if not target in [FileDestinations.LOCAL, FileDestinations.SDCARD]:
		return make_response("Unknown target: %s" % target, 404)

	if not _verifyFileExists(target, filename):
		return make_response("File not found on '%s': %s" % (target, filename), 404)

	# prohibit deleting files that are currently in use
	currentOrigin, currentFilename = _getCurrentFile()
	if currentFilename == filename and currentOrigin == target and (printer.is_printing() or printer.is_paused()):
		make_response("Trying to delete file that is currently being printed: %s" % filename, 409)

	if (target, filename) in fileManager.get_busy_files():
		make_response("Trying to delete a file that is currently in use: %s" % filename, 409)

	# deselect the file if it's currently selected
	if currentFilename is not None and filename == currentFilename:
		printer.unselect_file()

	# delete it
	if target == FileDestinations.SDCARD:
		printer.delete_sd_file(filename)
	else:
		fileManager.remove_file(target, filename)

	return NO_CONTENT

def _getCurrentFile():
	currentJob = printer.get_current_job()
	if currentJob is not None and "file" in currentJob.keys() and "name" in currentJob["file"] and "origin" in currentJob["file"]:
		return currentJob["file"]["origin"], currentJob["file"]["name"]
	else:
		return None, None


