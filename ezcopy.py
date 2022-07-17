#!/usr/bin/env python3

import sys
from pathlib import Path
import datetime
import os
import subprocess
import shutil
from colorama import Fore

'''python3 /home/sdf/Code/ezsdcopier/ezcopy2_test2.py [--FLAG] [SD_CARD_NAME]'''

# rsync canon powershot SD card photos
def copy_canon_photos():
	source = str(dcim_path)
	dest = str(photo_archive_path / canon_folder_name)
	logfile_name = canon_folder_name + "_RSYNC.log"
	logfile_path = photo_archive_path / logfile_name
	copy_count_str = '0'
	output_list = []
	print("\nCopying images from " + green(bold(source)) + " to " + green(bold(dest)) + "\n")

	# cmd = ['rsync', '-avEX', '--dry-run', '--stats', source+"/", dest, f"--log-file={rsync_logfile_path}"]
	cmd = ['rsync', '-avEX', '--stats', source+"/", dest, f"--log-file={logfile_path}"]
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

	# print rsync output in real time
	while proc.poll() is None:
		line = proc.stdout.readline().decode()
		line = line.strip()
		print(yellow(line))
		output_list.append(line)
	
	# get file count from rsync output
	for item in output_list:
		if "Number of created files:" in item:
			copy_count_str = item.split("Number of created files:")[-1]


	print("\nAppended to logfile at: " + green(bold(str(logfile_path))))
	print()
	print(green(bold(str(copy_count_str.strip()))) + " items copied")
	print()

# copy files from nikon D3200 SD card while sorting into folders by date taken
def copy_nikon_photos():
	src = dcim_path
	dest = photo_archive_path / nikon_folder_name
	logfile_name = nikon_folder_name + "_CUSTOMSYNC.log"
	logfile_path = photo_archive_path / logfile_name
	stdout_list = []
	copy_count = 0
	nested_dirs_found = 0
	new_dir_count = 0
	print("\nCopying images from " + green(bold(src)) + " to " + green(bold(dest)) + "\n")

	photo_folders = [*src.iterdir()]
	for folder in photo_folders:
		photo_list = [*folder.iterdir()]
		for photo_path in photo_list:
			dated_foldername = create_dated_foldername(photo_path)
			dated_folder_path = dest / dated_foldername
			photo_dest = dated_folder_path / photo_path.name

			if not dated_folder_path.exists():
				dated_folder_path.parent.mkdir(exist_ok=True)
				dated_folder_path.mkdir()
				print("\nCreated new folder " + green(bold(dated_folder_path)))
				stdout_list.append("\nCreated new folder " + str(dated_folder_path))
				new_dir_count += 1

			if not photo_dest.exists() and not photo_path.is_dir():
				log_line = str(photo_path) + " --> " + str(photo_dest)
				print(yellow(log_line))
				stdout_list.append(log_line + "\n")
				if photo_dest.suffix != '':
					shutil.copy2(photo_path, dated_folder_path, follow_symlinks=False)
				copy_count += 1

			elif photo_path.is_dir():
				nested_dir_message = "ITEM NOT COPIED: \'" + str(photo_path) + "\' is a nested directory\n"
				stdout_list.append(nested_dir_message)
				print(red(nested_dir_message))
				nested_dirs_found += 1
		print()

	add_to_logfile(logfile_path, stdout_list)

	print()
	print(green(bold(str(copy_count))) + " items copied")
	print(green(bold(str(new_dir_count))) + " new folders created")
	if nested_dirs_found > 0:
		print(red(bold(nested_dirs_found) + " nested directories found (not copied)"))
	print()

def create_dated_foldername(image_path):
	mtime = Path(image_path).stat().st_mtime
	date = datetime.datetime.fromtimestamp(mtime)
	yyyy = str(date.year)
	mm = str(date.month)
	dd = str(date.day)
	return f"{yyyy}_{mm}_{dd}"

# currently only used during nikon D3200 copying
def add_to_logfile(log_path, stdout, *args):
	print("\nAppending to logfile at: " + green(bold(str(log_path))))

	with open(log_path, 'a') as f:
		f.write("-"*30 + " BEGIN RUN " + "-"*30 + "\n")
		f.write("TIMESTAMP: " + str(datetime.datetime.now()) + "\n\n")

		if isinstance(stdout, str):
			f.write(stdout)
		elif isinstance(stdout, list):
			for line in stdout:
				f.write(line)

		for stderr in args:
			if stderr != '':
				f.write("ERRORS: \n")
				f.write(stderr)
		f.write("\n" + "-"*31 + " END RUN " + "-"*31 + "\n\n\n")

def green(string):
	string = str(string)
	return Fore.GREEN + string + Fore.RESET

def yellow(string):
	string = str(string)
	return Fore.YELLOW + string + Fore.RESET

def red(string):
	string = str(string)
	return Fore.RED + string + Fore.RESET

def blue(string):
	string = str(string)
	return Fore.BLUE + string + Fore.RESET

def bold(string):
	string = str(string)
	return "\033[1m" + string + "\033[22m"

def fade(string):
	string = str(string)
	return "\033[2m" + string + "\033[22m"

def print_header():
	print(bold(blue("\n\n\n\nEZSDCOPIER Launching...\n")))
	print("COMMAND: ")
	print(bold(yellow(f"    {sys.executable} {os.path.realpath(__file__)} {camera_flag} {sdcard_name}")))
	print("...............................")
	print("FLAG:  " + bold(camera_flag))
	print("DEVICE NAME:  " + bold(sdcard_name))
	print("...............................")
	print()

def print_exit():
	print(fade("\n ...Exiting program now...\n"))


canon_folder_name = "canon_powershot_SX50HS"
nikon_folder_name = "nikon_d3200"

photo_archive_path = Path("/home/" + os.environ["USER"] + "/Photo_Archive/")
media_path = Path("/media/" + os.environ["USER"])

args = sys.argv
canon_flags = ['-c', '--canon']
nikon_flags = ['-n', '--nikon']
if len(args) == 3:
	try:
		# determine if first or second argument is the flag for camera brand option
		if args[1][0] == "-":
			camera_flag = args[1]
			sdcard_name = args[2]
		elif args[2][0] == "-":
			camera_flag = args[2]
			sdcard_name = args[1]

		print_header()

		sdcard_path = media_path / sdcard_name

		# check for device in media directory
		media_sources = [*media_path.iterdir()]
		if sdcard_path not in media_sources:
			raise ValueError("Couldn't find device: " + bold(str(sdcard_path)) + "\nMake sure the device is plugged in and mounted.")
		
		# check for DCIM folder in SD card's main directory
		sdcard_dir_contents = [*sdcard_path.iterdir()]
		dcim_path = sdcard_path / "DCIM"
		if dcim_path not in sdcard_dir_contents:
			raise ValueError("Couldn't find DCIM folder in: " + bold(str(sdcard_path)))

		# set destination paths based on user input flag
		if camera_flag in canon_flags:
			copy_canon_photos()

		elif camera_flag in nikon_flags:
			copy_nikon_photos()

		else:
			raise ValueError("Not a recognized option: " + bold(camera_flag) + "\n  Try one of the following: " + bold(f"'{canon_flags[0]}', '{canon_flags[1]}', '{nikon_flags[0]}', '{nikon_flags[1]}'"))

		print(green("Process completed"))
		print_exit()

	except ValueError as v:
		print()
		print(red("Error: "))
		print(red("  " + str(v)))
		print_exit()

	except FileNotFoundError as e:
		print(red("File Not Found: "))
		print(red("Couldn't find " + bold(e.filename)))
		print_exit()
	
else:
	print(red("\nThis function only accepts 2 parameters.\n"))
	print(red("USAGE: "))
	print(f"     /bin/python3 {os.path.realpath(__file__)} " + bold("[FLAG] [SD_CARD_NAME]"))
	print(red("NOTE: Put DEVICE_NAME in single (\') or double (\") quotes if it contains spaces."))
	print(red("\n\tcamera options (flags): "))
	print(red("\t  -n,--nikon    Sorts images into " + bold("Nikon D3200") + " camera folder"))
	print(red("\t  -c,--canon    Sorts images into " + bold("Canon Powershot SX50 HS") + " camera folder"))
	print(f"\nExample:    /bin/python3 {os.path.realpath(__file__)} --canon CANON_DC")


###### Initial copy variables ######
# photo_archive_path = Path("/home/sdf/Photo_Archive2/")
# media_path = Path("/home/" + os.environ["USER"] + "/Photo_Archive") 
# shortcuts_home_path = Path("/home/" + os.environ["USER"] + "/Pictures2")
###### Initial copy commands ######
# /bin/python3 /home/sdf/Code/ezsdcopier/ezcopy.py -c canon_powershot_SX50HS
# /bin/python3 /home/sdf/Code/ezsdcopier/ezcopy.py -n nikon_d3200

