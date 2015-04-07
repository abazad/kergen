import subprocess

class PCI_Modalias_info:
    def __init__(self, modalias):
        self.modalias = modalias.replace('*','').replace('pci:','')
        self.vendor = self.modalias[self.modalias.find('v')+1:self.modalias.find('d')]
        self.device = self.modalias[self.modalias.find('d')+1:self.modalias.find('sv')]
        self.subvendor = self.modalias[self.modalias.find('sv')+2:self.modalias.find('sd')]
        self.subdevice = self.modalias[self.modalias.find('sd')+2:self.modalias.find('bc')]
        self.bus_class = self.modalias[self.modalias.find('bc')+2:self.modalias.find('sc')]
        self.bus_subclass = self.modalias[self.modalias.find('sc')+2:self.modalias.find('i')]
        self.interface = self.modalias[self.modalias.find('i')+1:]

    def compare_to(self, other):
        if not other.vendor or other.vendor in self.vendor:
            if not other.device or other.device in self.device:
                if not other.subvendor or other.subvendor in self.subvendor:
                    if not other.subdevice or other.subdevice in self.subdevice:
                        if not other.bus_class or other.bus_class in self.bus_class:
                            if not other.bus_subclass or other.bus_subclass in self.bus_subclass:
                                if not other.interface or other.interface in self.interface:
                                    return True
        return False


class USB_Modalias_info:
    def __init__(self, modalias):
        self.modalias = modalias.replace('*','').replace('usb:','')
        self.device_vendor = self.modalias[self.modalias.find('v')+1:self.modalias.find('p')]
        self.device_product = self.modalias[self.modalias.find('p')+1:self.modalias.find('d')]
        self.bcdevice = self.modalias[self.modalias.find('d')+1:self.modalias.find('dc')]
        self.device_class = self.modalias[self.modalias.find('dc')+2:self.modalias.find('dsc')]
        self.device_subclass = self.modalias[self.modalias.find('dsc')+3:self.modalias.find('dp')]
        self.device_protocol = self.modalias[self.modalias.find('dp')+2:self.modalias.find('ic')]
        self.interface_class = self.modalias[self.modalias.find('ic')+2:self.modalias.find('isc')]
        self.interface_subclass = self.modalias[self.modalias.find('isc')+3:self.modalias.find('ip')]
        self.interface_protocol = self.modalias[self.modalias.find('ip')+2:]

    def compare_to(self, other):
        if not other.device_vendor or other.device_vendor in self.device_vendor:
            if not other.device_product or other.device_product in self.device_product:
                if not other.bcdevice or other.bcdevice in self.bcdevice:
                    if not other.device_class or other.device_class in self.device_class:
                        if not other.device_subclass or other.device_subclass in self.device_subclass:
                            if not other.device_protocol or other.device_protocol in self.device_protocol:
                                if not other.interface_class or other.interface_class in self.interface_class:
                                    if not other.interface_subclass or other.interface_subclass in self.interface_subclass:
                                        if not other.interface_protocol or other.interface_protocol in self.interface_protocol:
                                            return True
        return False


class SCSI_Modalias_info:
    def __init__(self, modalias):
        self.modalias = modalias.replace('*','')

    def compare_to(self, other):
        if not other.modalias or other.modalias in self.modalias:
            return True
        return False


class SCSI_Module:
    def __init__(self, modalias, module):
        self.modalias = SCSI_Modalias_info(modalias)
        self.module = module


class PCI_Module:
    def __init__(self, modalias, module):
        self.modalias = PCI_Modalias_info(modalias)
        self.module = module


class USB_Module:
    def __init__(self, modalias, module):
        self.modalias = USB_Modalias_info(modalias)
        self.module = module

class Device:
    def __init__(self, module):
        self.module = module.replace('_', '-')
        self.kernel_option = self.get_kernel_option()

        if not self.kernel_option and '-' in self.module:
            self.module = module.replace('-','_')
            self.kernel_option = self.get_kernel_option()

    def get_kernel_option(self):
        grep_command = 'grep -Ri --include Makefile " ' + self.module + '\.o" /usr/src/linux/|grep CONFIG_ || true'
        kernel_option = subprocess.check_output(grep_command, shell=True, universal_newlines=True)
        if kernel_option:
            kernel_option = kernel_option[kernel_option.rfind('(')+1:kernel_option.rfind(')')] 
        return kernel_option


def generate_device_kernel_options():
    #pci
    sys_pci_info_list = subprocess.check_output('cat /sys/bus/pci/devices/*/modalias', shell=True, universal_newlines=True)
    sys_pci_info_list = sys_pci_info_list.split('\n')
    sys_pci_info_list = [PCI_Modalias_info(line) for line in sys_pci_info_list if line]
    #usb
    sys_usb_info_list = subprocess.check_output('cat /sys/bus/usb/devices/*/modalias', shell=True, universal_newlines=True)
    sys_usb_info_list = sys_usb_info_list.split('\n')
    sys_usb_info_list = [USB_Modalias_info(line) for line in sys_usb_info_list if line]
    #scsi
    sys_scsi_info_list = subprocess.check_output('cat /sys/block/*/device/modalias', shell=True, universal_newlines=True)
    sys_scsi_info_list = sys_scsi_info_list.split('\n')
    sys_scsi_info_list = [SCSI_Modalias_info(line) for line in sys_scsi_info_list if line and 'scsi:' in line]

    #generating the kernel modules info
    all_pci_modules_list = []
    all_usb_modules_list = []
    all_scsi_modules_list = []
    with open('modules.alias', 'r') as module_alias:
        for line in module_alias:
            if line[6:10] == 'usb:':
                all_usb_modules_list.append(USB_Module(line[6:line.rfind(' ')], line[line.rfind(' ')+1:-1]))
            elif line[6:10] == 'pci:':
                all_pci_modules_list.append(PCI_Module(line[6:line.rfind(' ')], line[line.rfind(' ')+1:-1]))
            elif line[6:11] == 'scsi:':
                all_scsi_modules_list.append(SCSI_Module(line[6:line.rfind(' ')], line[line.rfind(' ')+1:-1]))

    #generating the devices
    devices = []
    for sys_pci_info in sys_pci_info_list:
        for pci_module in all_pci_modules_list:
            if sys_pci_info.compare_to(pci_module.modalias):
                devices.append(Device(pci_module.module))
    for sys_usb_info in sys_usb_info_list:
        for usb_module in all_usb_modules_list:
            if sys_usb_info.compare_to(usb_module.modalias):
                devices.append(Device(usb_module.module))
    for sys_scsi_info in sys_scsi_info_list:
        for scsi_module in all_scsi_modules_list:
            if sys_scsi_info.compare_to(scsi_module.modalias):
                devices.append(Device(scsi_module.module))

    #generating kernel options list
    kernel_options = [device.kernel_option for device in devices]

    return kernel_options

def generate_file_system_kernel_options():
    fs_info = subprocess.check_output('mount | grep \/dev\/sd', shell=True, universal_newlines=True)[:-1]
    fs_info = fs_info.split('\n')
    options_list = []
    for line in fs_info:
        option = line[line.find(' type ')+6:]
        option = option[:option.find(' ')].upper() + '_FS'
        options_list.append(option)
    options_list = list(set(options_list))
    return options_list


file_system_kernel_options = generate_file_system_kernel_options()
device_kernel_options = generate_device_kernel_options()
all_options = device_kernel_options + file_system_kernel_options
print(' '.join(all_options))