'''
Evenger create EVE-NG network topology with EVE-NG API and excel file

Version: 2023.01.09
'''
import json
import logging
import os
import telnetlib
import time
from dataclasses import dataclass

import pandas as pd
import requests
from jinja2 import Template


# LOG OPTIONS
logging.basicConfig(
    handlers=[
        logging.StreamHandler()
    ],
    format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level='INFO'
)

requests.packages.urllib3.disable_warnings()


@dataclass
class Evenger:
    """ evenger class

    ### Args:
        - eveng_server_url : http://172.18.18.18
        - username : admin
        - password : admin
        - lab_path : my_lab_folder/my_lab_1

    """
    eveng_server_url: str
    username: str
    password: str
    lab_path: str

    def __post_init__(self):
        self._cookie = self._get_cookie()
        self._node_name_id_dict = {}
        self._nodename_interface_id_dict = {}
        self._bridge_name_id_dict = {}

    def _get_cookie(self):
        authentication_data = {
            'username': self.username,
            'password': self.password,
            "html5": "-1"
        }
        authentication_data = json.dumps(authentication_data)
        try:
            res = requests.post(f'{self.eveng_server_url}/api/auth/login',
                                verify=False,
                                data=authentication_data, timeout=5)
            cookie = res.cookies
            logging.info(res.text)
            return cookie
        except Exception as e:
            logging.error(
                f'GET COOKIE PROBLEM <{self.eveng_server_url}/api/auth/login>: {e}')
            return None

    def _get(self, url):
        try:
            res = requests.get(f'{self.eveng_server_url}{url}',
                               cookies=self._cookie, verify=False)
            logging.debug(res.text)
            return res.json()
        except Exception as e:
            logging.error(f'GET PROBLEM <{self.eveng_server_url}{url}> : {e}')
            return None

    def _post(self, url, json_text):
        try:
            res = requests.post(
                f'{self.eveng_server_url}{url}',
                cookies=self._cookie,
                json=json.loads(json_text),
                verify=False)
            try:
                logging.info(res.text)
                return res.json()
            except:
                return res.text
        except Exception as e:
            logging.error(
                f'POST PROBLEM <{self.eveng_server_url}{url}> <{json_text}>: {e}')
            return None

    def _put(self, url, json_text):
        try:
            res = requests.put(
                f'{self.eveng_server_url}{url}',
                cookies=self._cookie,
                json=json.loads(json_text),
                verify=False)
            try:
                logging.info(res.text)
                return res.json()
            except:
                return res.text
        except Exception as e:
            logging.error(
                f'PUT PROBLEM <{self.eveng_server_url}{url}> <{json_text}>: {e}')
            return None

    def _node_name_id_dict_create(self):
        if self._node_name_id_dict:
            return self._node_name_id_dict
        nodes_dict = self._get(
            f'/api/labs/{self.lab_path}.unl/nodes')['data']
        self._node_name_id_dict = {v['name']: k for k, v in nodes_dict.items()}
        return self._node_name_id_dict

    def _nodename_interface_id_dict_create(self):
        ''' node : {int : id, int2 : id2 }, node2 :'''
        if self._nodename_interface_id_dict:
            return self._nodename_interface_id_dict
        result_dict = {}
        for node_name, node_id in self._node_name_id_dict_create().items():
            node_int_list = self._get(
                f'/api/labs/{self.lab_path}.unl/nodes/{node_id}/interfaces')['data']['ethernet']
            result_dict[node_name] = {v['name']: str(
                i) for i, v in enumerate(node_int_list)}
        self._nodename_interface_id_dict = result_dict
        return self._nodename_interface_id_dict

    def _bridge_name_id_dict_create(self):
        if self._bridge_name_id_dict:
            return self._bridge_name_id_dict
        bridge_dict = self._get(
            f'/api/labs/{self.lab_path}.unl/networks')['data']
        self._bridge_name_id_dict = {
            v['name']: k for k, v in bridge_dict.items() if str(v['visibility']) == '1'}
        return self._bridge_name_id_dict

    @staticmethod
    def _send_telnet_commands(commands_text, node_ip, node_port):
        """ Send telnet commands with _EXCEPT and _SLEEP options

        Example commands_text:

        ```py
        telnet_commands_text = '''
            _EXPECT: ogin
            admin
            _EXPECT: assword
            admin
            _SLEEP: 1
            _EXPECT: #
            configure
        '''
        ```
        """
        commands_line = [i.strip()
                         for i in commands_text.splitlines() if i.strip() != '']
        try:
            except_line = ''
            timeout_line = 5
            temp_sleep = 0
            outputs = ''
            with telnetlib.Telnet(node_ip, int(node_port)) as tn:
                for i in commands_line:
                    if i.startswith('_EXPECT:'):
                        except_line = i.removeprefix('_EXPECT:').strip()
                        continue
                    if i.startswith('_TIMEOUT:'):
                        timeout_line = int(i.removeprefix('_TIMEOUT:').strip())
                        continue
                    if i.startswith('_SLEEP:'):
                        temp_sleep = int(i.removeprefix('_SLEEP:').strip())
                        time.sleep(temp_sleep)
                        continue
                    if except_line:
                        output = tn.read_until(
                            except_line.encode(), timeout=timeout_line)
                        outputs += str(output, encoding='ascii')
                        tn.write(i.encode('ascii')+b'\n')
                        outputs += str(tn.read_eager(), encoding='ascii')
                    else:
                        tn.write(i.encode('ascii')+b'\n')
                        outputs += str(tn.read_eager(), encoding='ascii')
            return outputs
        except Exception as e:
            logging.error(f'Telnet problem {node_ip} {node_port} : {e}')
            return None

    def add_lab(self, **lab_args):
        """ Add new lab (check path-name not exist on eveng)

        ### Args:
            - description (optional) : lab description

        """
        path_name_list = self.lab_path.rsplit('/', maxsplit=1)
        if len(path_name_list) == 1:
            lab_args['name'] = path_name_list[0]
            lab_args['path'] = '/'
        else:
            lab_args['name'] = path_name_list[1]
            lab_args['path'] = '/' + path_name_list[0]

        json_text = '''
        {
        "author": "",
        "description": "{{description}}",
        "scripttimeout": 300,
        "version": 1,
        "name": "{{name}}",
        "body": "",
        "path": "{{path}}"
        }
        '''

        self._post(f'/api/labs', Template(json_text).render(lab_args))
        logging.info(f'add_lab {lab_args} done!')

    def add_node_custom(self, **node_args):
        """Add node custom with custom_json_text (Jinja template) to lab
        One of the node_args key must be <custom_json_text> other depends on Jinja template and optional

        ### Args:
            - custom_json_text (mandatory): custom node json data text (Jinja template)

        ### Returns:
            - node id (str) : 1

        """
        res = self._post(f'/api/labs/{self.lab_path}.unl/nodes',
                         Template(node_args['custom_json_text']).render(node_args))
        logging.info(f'add_node_custom {node_args} done!')
        return res['data']['id']

    def add_node_sros_cpm(self, **node_args):
        """Add node sros-cpm to lab

        ### Args:
            - image : timoscpm-20.7.R2
            - name : 7750_test_1
            - management_address : 10.1.1.1/24
            - timos_line : slot=A chassis=SR-12 card=cpm5
            - timos_license : license.txt or ftp://10.1.1.254/license.txt
            - left (str) : 200
            - top (str) : 200

        ### Returns:
            - node id (str) : 1

        """
        json_text = '''
        {
        "template":"timoscpm",
        "type":"qemu",
        "count":"1",
        "image":"{{image}}",
        "name":"{{name}}",
        "icon":"SROS.png",
        "uuid":"",
        "cpulimit":"undefined",
        "cpu":"1",
        "ram":"2048",
        "ethernet":"2",
        "management_address":"{{management_address}}",
        "timos_line":"{{timos_line}}",
        "timos_license":"{{timos_license}}",
        "qemu_version":"","qemu_arch":"",
        "qemu_nic":"",
        "qemu_options":"-machine type=pc,accel=kvm -serial mon:stdio -nographic -no-user-config -nodefaults -rtc base=utc",
        "ro_qemu_options":"-machine type=pc,accel=kvm -serial mon:stdio -nographic -no-user-config -nodefaults -rtc base=utc",
        "config":"0",
        "delay":"0",
        "console":"telnet",
        "left":"{{left}}",
        "top":"{{top}}",
        "postfix":0
        }
        '''
        res = self._post(f'/api/labs/{self.lab_path}.unl/nodes',
                         Template(json_text).render(node_args))
        logging.info(f'add_node_sros_cpm {node_args} done!')
        return res['data']['id']

    def add_node_sros_iom(self, **node_args):
        """Add node sros-iom to lab

        ### Args:
            - image : timosiom-20.7.R2
            - name : 7750_iom_test_1
            - timos_line : slot=1 chassis=SR-12 card=iom3-xp-b mda/1=m10-1gb-sfp-b mda/2=isa-bb
            - left (str) : 200
            - top (str) : 200

        ### Returns:
            - node id (str) : 1

        """

        json_text = '''
        {
        "template":"timosiom",
        "type":"qemu",
        "count":"1",
        "image":"{{image}}",
        "name":"{{name}}",
        "icon":"SROS linecard.png",
        "uuid":"",
        "cpulimit":"undefined",
        "cpu":"1",
        "ram":"2048",
        "ethernet":"10",
        "timos_line":"{{timos_line}}",
        "qemu_version":"",
        "qemu_arch":"",
        "qemu_nic":"",
        "qemu_options": "-machine type=pc,accel=kvm -serial mon:stdio -nographic -no-user-config -nodefaults -rtc base=utc",
        "ro_qemu_options":"-machine type=pc,accel=kvm -serial mon:stdio -nographic -no-user-config -nodefaults -rtc base=utc",
        "config":"0",
        "delay":"0",
        "console":"telnet",
        "left":"{{left}}",
        "top":"{{top}}",
        "postfix":0
        }
        '''
        res = self._post(f'/api/labs/{self.lab_path}.unl/nodes',
                         Template(json_text).render(node_args))
        logging.info(f'add_node_sros_iom {node_args} done!')
        return res['data']['id']

    def add_node_linux(self, **node_args):
        """Add node linux server to lab

        ### Args:
            - image : linux-centos7
            - name : centos7_server
            - cpu (str) : 1
            - ram (str) : 1024
            - left (str) : 200
            - top (str) : 200

        ### Returns:
            - node id (str) : 1

        """
        json_text = '''
        {
        "template": "linux",
        "type": "qemu",
        "count": "1",
        "image": "{{image}}",
        "name": "{{name}}",
        "icon": "Server.png",
        "uuid": "",
        "cpulimit": "undefined",
        "cpu": "{{cpu}}",
        "ram": "{{ram}}",
        "ethernet": "2",
        "firstmac": "",
        "qemu_version": "",
        "qemu_arch": "",
        "qemu_nic": "",
        "qemu_options": "-machine type=pc,accel=kvm -vga virtio -usbdevice tablet -boot order=cd",
        "ro_qemu_options": "-machine type=pc,accel=kvm -vga virtio -usbdevice tablet -boot order=cd",
        "config": "0",
        "delay": "0",
        "console": "vnc",
        "left": "{{left}}",
        "top": "{{top}}",
        "postfix": 0
        }
        '''
        res = self._post(f'/api/labs/{self.lab_path}.unl/nodes',
                         Template(json_text).render(node_args))
        logging.info(f'add_node_linux {node_args} done!')
        return res['data']['id']

    def add_network(self, **network_args):
        """Add network (bridge) to lab

        ### Args:
            - name : Bridge_INTERNAL
            - type : bridge or pnet0
            - left (str) : 200
            - top (str) : 200

        ### Returns:
            - network/bridge id (str) : 1

        """
        json_text = '''
        {
        "count": "1",
        "visibility": "1",
        "name": "{{name}}",
        "type": "{{type}}",
        "left": "{{left}}",
        "top": "{{top}}",
        "postfix": 0
        }
        '''

        res = self._post(f'/api/labs/{self.lab_path}.unl/networks',
                         Template(json_text).render(network_args))
        logging.info(f'add_network {network_args} done!')
        return res['data']['id']

    def connect_node_to_bridge(self, node_name, node_port, bridge_name):
        """create connection between node and bridge
        (!!! before create connection, all bridge and node should be already created !!!)

        ### Args:
            - node_name : 7750_test_1
            - node_port : Mgmt or SF or 1/1/1
            - bridge_name : Bridge_internal

        """

        node_id = self._node_name_id_dict_create()[node_name]
        network_id = self._bridge_name_id_dict_create()[bridge_name]
        int_id = self._nodename_interface_id_dict_create()[
            node_name][node_port]
        self._put(f'/api/labs/{self.lab_path}.unl/nodes/{node_id}/interfaces',
                  f'{{"{int_id}":{network_id}}}')
        logging.info(
            f'connect_node_to_bridge {node_name}, {node_port}, {bridge_name} done!')

    def connect_node_to_node(self, first_node, first_port, second_node, second_port):
        """create connection between nodes
        (!!! before create connection, all bridge and node should be already created !!!)

        ### Args:
            - first_node : 7750_test_1
            - first_port : SF or 1/1/1
            - second_node : 7750_test_2
            - second_port : SF or 1/1/1

        """
        network_dict_invisible = {
            'name': 'Bridge_invisible',
            'type': 'bridge',
            'left': '500',
            'top': '500'
        }

        network_id = self.add_network(**network_dict_invisible)
        first_node_id = self._node_name_id_dict_create()[first_node]
        second_node_id = self._node_name_id_dict_create()[second_node]
        first_int_id = self._nodename_interface_id_dict_create()[
            first_node][first_port]
        second_int_id = self._nodename_interface_id_dict_create()[
            second_node][second_port]

        self._put(f'/api/labs/{self.lab_path}.unl/nodes/{first_node_id}/interfaces',
                  f'{{"{first_int_id}":{network_id}}}')
        self._put(f'/api/labs/{self.lab_path}.unl/nodes/{second_node_id}/interfaces',
                  f'{{"{second_int_id}":{network_id}}}')

        self._put(f'/api/labs/{self.lab_path}.unl/networks/{network_id}',
                  '{"visibility":"0"}')
        logging.info(
            f'connect_node_to_node {first_node}, {first_port}, {second_node}, {second_port} done!')

    def config_with_telnet(self, config_folder='configs', log_debug=False):
        """ make configuration for all nodes via eve-ng telnet
        (in config_folder, config file must be same as eve-ng node name with .txt extension e.g. node_1.txt)

        Example node_1.txt file:

        ```
        _EXPECT: ogin
        admin
        _EXPECT: assword
        admin
        _EXPECT: #
        configure
            service
                vprn ...
        ```

        ### Args:
            - config_folder : configs

        """
        all_nodes_dict = self._get(
            f'/api/labs/{self.lab_path}.unl/nodes')['data']
        all_nodes_telnet_url = {
            v['name']: v['url'].split('//')[1] for k, v in all_nodes_dict.items() if v['url'].startswith('telnet')
        }
        for node_name, node_telnet_url in all_nodes_telnet_url.items():
            if os.path.exists(f'{config_folder}/{node_name}.txt'):
                try:
                    with open(f'{config_folder}/{node_name}.txt') as file:
                        node_config_text = file.read()
                    node_telnet_ip, node_telnet_port = node_telnet_url.split(
                        ':')
                    node_telnet_result = self._send_telnet_commands(
                        node_config_text, node_telnet_ip, node_telnet_port)
                    if log_debug:
                        logging.info(
                            f'Telnet outputs for {node_name} {node_telnet_url}')
                        logging.info(node_telnet_result)
                    logging.info(
                        f'Telnet done for {node_name} {node_telnet_url}')
                except Exception as e:
                    logging.error(
                        f'Telnet problem for {node_name} {node_telnet_url}: {e}')

    @staticmethod
    def excel_topology(excel_filename, auto_start='NO', jump_server_name='', config_folder='', node_boot_time=180):
        """create topology from excel file

        ### Args:
            - excel_filename : evenger_create_lab_input.xlsx
            - auto_start : NO or YES (for configuration with telnet must be YES)
            - jump_server_name (optional) : SERVER_CENTOS7 (function will return <server_vnc_host, server_vnc_port> as tuple)
            - config_folder (optional) : my_configs_folder 
              (for making configuration with telnet, for detail info look <Evenger.config_with_telnet>)
            - node_boot_time (optional) : 180 (second) adjust node boot time for node configuration

        ### Return:
            - <server_vnc_host, server_vnc_port> as tuple (if jump_server_name set)

        """
        # get evenger object specs
        pd_evenger_sheet = pd.read_excel(
            excel_filename, sheet_name='_LAB_INFO', dtype=str,
            skiprows=[0]
        ).fillna('')
        header = [i.strip() for i in list(pd_evenger_sheet.keys())][1:]
        values = pd_evenger_sheet.iterrows()
        for i, v in values:
            v_strip = [i.strip() for i in v.to_list()[1:]]
            zip_line = {
                i: j for i, j in zip(header, v_strip) if j != ''
            }
            evenger_object = Evenger(**zip_line)
            break

        try:
            evenger_object.add_lab()
        except Exception as e:
            logging.error(
                f'Check Excel sheet <_LAB_INFO>, evenger object not created: {e}')
            raise SystemExit

        sheets = list(pd.ExcelFile(excel_filename).sheet_names)

        dir_module_funcs = [
            name for name in dir(Evenger) if not name.startswith('_')
        ]

        sheets_in_func = [i for i in sheets if i in dir_module_funcs]

        for sheet in sheets_in_func:
            pd_sheet = pd.read_excel(
                excel_filename, sheet_name=sheet, dtype=str,
                skiprows=[0]
            ).fillna('')
            # remove first column
            header = [i.strip() for i in list(pd_sheet.keys())][1:]
            values = pd_sheet.iterrows()
            for i, v in values:
                # remove first column
                v_strip = [i.strip() for i in v.to_list()[1:]]
                try:
                    zip_line = {i: j for i, j in zip(
                        header, v_strip) if j != ''}
                    evenger_func = getattr(evenger_object, sheet)
                    evenger_func(**zip_line)
                except Exception as e:
                    logging.error(
                        f'Excel sheet <{sheet}> line <{v_strip}> not completed: {e}')
        # start nodes if auto_start is True
        try:
            if auto_start == 'YES':
                evenger_object._get(
                    f'/api/labs/{evenger_object.lab_path}.unl/nodes/start')
                logging.info(f'Nodes started for {evenger_object.lab_path}')
                # wait boot time and run telnet configuration if config_folder
                try:
                    if config_folder:
                        logging.info(
                            f'Node boot time waiting for <{node_boot_time} seconds>')
                        time.sleep(int(node_boot_time))
                        evenger_object.config_with_telnet(
                            config_folder=config_folder)
                        logging.info(
                            f'Telnet configs for <{config_folder}/*> done!')
                except Exception as e:
                    logging.error(
                        f'Telnet configs for <{config_folder}/*> failed: {e}')
        except Exception as e:
            logging.error(
                f'Nodes start failed: {e}')

        # return jump server vnc host/port
        try:
            if jump_server_name:
                server_id = evenger_object._node_name_id_dict_create()[
                    jump_server_name]
                server_vnc_url = evenger_object._get(
                    f'/api/labs/{evenger_object.lab_path}.unl/nodes/{server_id}')['data']['url']
                server_vnc_host, server_vnc_port = server_vnc_url.replace(
                    'vnc://', '').split(':')
                return server_vnc_host, server_vnc_port
        except Exception as e:
            logging.error(
                f'Jump_server {jump_server_name} vnc host/port failed: {e}')
