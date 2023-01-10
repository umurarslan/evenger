# Evenger
Create EVE-NG network topology with EVE-NG API and excel file.

## Requirements

[Python >= 3.9](https://www.python.org/downloads/)

> For Windows, select the **Add Python 3.x to PATH** checkbox during installation.

---

## Installation

```
pip install .....................................
```

---

## Usage (API)

```py
from evenger import Evenger

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
# add bridge (network) to topology
evenger_lab.add_network(name='Bridge_INTERNAL',type='bridge',left='200',top='200')
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
# add custom node with eve-ng node json data

```
