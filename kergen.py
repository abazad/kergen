import subprocess
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--menuconfig', help='Opens a kernel configuration menu at the end of all other operations, but prior build', action='store_true')
parser.add_argument('-n', '--new',        help='Start from scratch without using any existing config files (runs "make mrproper" and "make defconfig")', action='store_true')
parser.add_argument('-u', '--upgrade',    help='Select the newest installed kernel version and if --new is not used copy the old .config file and run "make olddefconfig".', action='store_true')
parser.add_argument('-b', '--build',      help='Build a new kernel and copy it in /boot', action='store_true')
parser.add_argument('-g', '--generate',   help='Generate optimized kernel options for your hardware and add the non existing ones to .config', action='store_true')
args = parser.parse_args()

if args.upgrade:
    #get info from "eselect kernel"
    eselect_kernel_out = subprocess.check_output(['eselect', 'kernel', 'list'], universal_newlines=True)
    eselect_kernel_out = eselect_kernel_out[eselect_kernel_out.find('\n') + 1 : eselect_kernel_out.rfind('\n')]

    #check if the newest installed version is selected
    if eselect_kernel_out[-1] == '*':
        print('The newest installed kernel version is already selected.')
    else:
        #save the old .config path before changing the symlink
        if not args.new:
            oldconfig_path = subprocess.check_output(['realpath', '/usr/src/linux/.config'], universal_newlines=True).strip('\n')

        #select the newest kernel version
        print('The following kernel versions are installed:\n' + eselect_kernel_out + '\n')
        eselect_newest_num = eselect_kernel_out.count('\n') + 1
        subprocess.check_call(['eselect', 'kernel', 'set', str(eselect_newest_num)])
        print('Changed selected version to:' + eselect_kernel_out[eselect_kernel_out.rfind('\n'):] + ' *\n')

        #copy the old .config
        if not args.new and os.path.isfile(oldconfig_path):
            print('--new is not used, so we are using the .config from the old version.\n'
                  'Copying "' + oldconfig_path + '"" to "/usr/src/linux/"...')
            subprocess.check_call(['cp', oldconfig_path, '/usr/src/linux/.config'])

    #make olddefconfig
    if not args.new and os.path.isfile('/usr/src/linux/.config'):
        print('Creating .config file by using the valid options of the old .config...')
        subprocess.check_call(['make', 'olddefconfig'], cwd='/usr/src/linux')

if args.new or not os.path.isfile('/usr/src/linux/.config'):
    subprocess.check_call(['make', 'mrproper'], cwd='/usr/src/linux')
    subprocess.check_call(['make', 'defconfig'], cwd='/usr/src/linux')

if args.generate:
    kernel_options = subprocess.check_output(['python', 'kergen-map.py'], universal_newlines=True)[:-1].split(' ')
    subprocess.check_call(['python', 'depgen.py'] + kernel_options, universal_newlines=True)

if args.menuconfig:
    subprocess.check_call(['make', 'menuconfig'], cwd='/usr/src/linux')

if args.build:
    subprocess.check_call(['make', 'olddefconfig'], cwd='/usr/src/linux')
    subprocess.check_call(['make', 'clean'], cwd='/usr/src/linux')
    subprocess.check_call(['make'], cwd='/usr/src/linux')
    subprocess.check_call('cd /usr/src/linux && make modules_install || true', shell=True)
    subprocess.check_call(['make', 'install'], cwd='/usr/src/linux')
    print("The new kernel has been built and installed in the /boot directory.\n"
          "If you are using any external kernel modules, you can rebuild them using 'emerge @module-rebuild'.\n"
          "And don't forget to update your bootloader configuration :).")