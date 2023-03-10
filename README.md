# Evenger
Create EVE-NG network topology with EVE-NG API and excel file.

---

## Requirements

[Python >= 3.9](https://www.python.org/downloads/)

> For Windows, select the **Add Python 3.x to PATH** checkbox during installation.

---

## Installation

```
pip install evenger
```

---

## Usage (API)

```py
# import Evenger
from evenger import Evenger
```

```py
# define Evenger object
evenger_lab = Evenger(
    eveng_server_url='http://172.18.18.18',
    username='admin',
    password='eve',
    lab_path='my_lab_folder/my_lab'
)
```

```py
# add NEW lab
evenger_lab.add_lab()
```

```py
# add regular bridge (network) to topology (type: bridge)
evenger_lab.add_network(
    name='Bridge_INTERNAL',
    type='bridge',
    left='200',
    top='200'
)

# add cloud bridge (network) to topology (type: pnet0)
evenger_lab.add_network(
    name='Bridge_MANAGEMENT',
    type='pnet0',
    left='700',
    top='200'
)
```

```py
# add node nokia sros
nokia_sros_cpm_node_dict = {
    'image': 'timoscpm-21.10.R6',
    'name': '7750_test_1',
    'management_address': '10.1.1.102/24',
    'timos_line': 'slot=A chassis=SR-12 card=cpm5',
    'timos_license': 'ftp://172.18.18.18/sros_vSIM_R21_license_file.txt',
    'left': '500',
    'top': '200'
}
evenger_lab.add_node_sros_cpm(**nokia_sros_cpm_node_dict)
```

```py
# add linux server
centos7_node_dict = {
    'image': 'linux-centos7',
    'name': 'centos7_server',
    'cpu': '1',
    'ram': '1024',
    'left': '700',
    'top': '700'
}
evenger_lab.add_node_linux(**centos7_node_dict)
```

```py
# add any custom node with eve-ng node json data (e.g. Cisco XRv 9000)
cisco_xrv_json_text='''
{
  "template": "xrv",
  "type": "qemu",
  "count": "1",
  "image": "xrv-k9-6.0.1",
  "name": "xrv_custom_node",
  "icon": "XR.png",
  "uuid": "",
  "cpulimit": "undefined",
  "cpu": "1",
  "ram": "3072",
  "ethernet": "4",
  "qemu_version": "",
  "qemu_arch": "",
  "qemu_nic": "",
  "qemu_options": "-machine type=pc,accel=kvm,usb=off -serial mon:stdio -nographic -no-user-config -nodefaults -rtc base=utc,driftfix=slew -global kvm-pit.lost_tick_policy=discard -no-hpet -realtime mlock=off -no-shutdown -boot order=c",
  "ro_qemu_options": "-machine type=pc,accel=kvm,usb=off -serial mon:stdio -nographic -no-user-config -nodefaults -rtc base=utc,driftfix=slew -global kvm-pit.lost_tick_policy=discard -no-hpet -realtime mlock=off -no-shutdown -boot order=c",
  "config": "0",
  "delay": "0",
  "console": "telnet",
  "left": "200",
  "top": "800",
  "postfix": 0
}
'''
evenger_lab.add_node_custom(custom_json_text=cisco_xrv_json_text)
```

---
> Before create any connection, all bridge and node should be already created. Do not add any node after connection.
---

```py
# connect node to bridge/network
evenger_lab.connect_node_to_bridge(
    node_name='7750_test_1',
    node_port='1/1/1',
    bridge_name='Bridge_Internal'
)
```

```py
# connect node to node
evenger_lab.connect_node_to_node(
    first_node='7750_test_1',
    first_port='1/1/1',
    second_node='7750_test_2',
    second_port='1/1/2'
)
```

---

## Usage (Node Configuration with Telnet)
- Create config folder in current working directory e.g. **my_config_folder**.
- Create txt file with eve-ng node name e.g. **7750_test_1.txt** in config folder (node must be booted completely and supported eve-ng telnet).
- Add cli configuration to node text file with **<_EXPECT: ***expected-string***>** which depends on node cli. Below example for Nokia SROS:

    ```
    _TIMEOUT: 3
    _EXPECT: ogin
    admin
    _EXPECT: assword
    admin
    _EXPECT: >config
    configure
        system
            name "7750_test_1_system_name"
        exit
    exit
    logout
    ```

- After that add node configs to config folder (my_config_folder/7750_test_1.txt, my_config_folder/7750_test_2.txt etc.) run below python code:
    ```py
    # import Evenger
    from evenger import Evenger
    ```
    
    ```py
    # define Evenger object
    evenger_lab = Evenger(
        eveng_server_url='http://172.18.18.18',
        username='admin',
        password='eve',
        lab_path='my_lab_folder/my_lab'
    )
    ```
    
    ```py
    # send configuration with telnet for eve-ng telnet supported node
    evenger_lab.config_with_telnet(config_folder='my_config_folder')
    ```

---

## Usage (Create Topology with Excel File)

Check **examples/evenger_topology.xlsx** excel file in project repo. 
"_LAB_INFO" sheet must be filled for eve-ng access and other sheets are same as API functions use regarding eve-ng topology. 

- Run from CLI:

    > With pip installation, **evenger** command is already added to system path.
    
    Help:
    ```
    PS C:\Users\alg\desktop> evenger -h
    usage: evenger.py [-h] [--excel_file EXCEL_FILE] [--config_folder CONFIG_FOLDER] [--auto_start AUTO_START] [--boot_time BOOT_TIME]

    optional arguments:
      -h, --help            show this help message and exit
      --excel_file EXCEL_FILE
                            excel file path [e.g. my_evenger_topology.xlsx] (default: --excel_file=evenger_topology.xlsx)
      --config_folder CONFIG_FOLDER
                            config folder path [e.g. my_configs_folder] (OPTIONAL default: --config_folder=configs)
      --auto_start AUTO_START
                            auto start [YES or NO] (default: --auto_start=YES)
      --boot_time BOOT_TIME
                            node boot time in seconds [e.g. 150] (default: --boot_time=180)
    ```
    
    > Run **evenger** command in working directory which includes excel file and/or config folder
    
    Run without config file:
    ```
    PS C:\Users\alg\desktop> evenger --excel_file my_evenger_topology.xlsx
    ```

    Run with config files folder:
    ```
    PS C:\Users\alg\desktop> evenger --excel_file my_evenger_topology.xlsx --config_folder my_configs_folder
    ```
    
- Run from python code:
    ```py
    # import Evenger only, no need create Evenger object
    from evenger import Evenger

    # create topology with excel file
    Evenger.excel_topology(
        excel_filename='evenger_topology.xlsx',
        auto_start='YES'
    )

    # create topology with excel and telnet configuration
    Evenger.excel_topology(
        excel_filename='evenger_topology.xlsx',
        auto_start='YES',
        config_folder='my_config_folder',
        node_boot_time=150
    )
    ```

