#! /usr/bin/env python

# Copyright 2016 Neverware Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Update vendors.py using the UEFI PNP vendor ID spreadsheet.

The spreadsheet can be downloaded here:

  http://www.uefi.org/uefi-pnp-export

Note that although the website claims it's an Excel spreadsheet and
gives it a .xls extension, it's really HTML. Hence the unexpected HTML
parsing below.

In case that link becomes stale, the parent pages are:

  http://www.uefi.org/pnp_id_list
  http://www.uefi.org/PNP_ACPI_Registry

"""

import argparse
import datetime
from os import path
from xml.etree import ElementTree

from bios_pnp import pnp


class State:
    """Spreadsheet parsing state enumeration."""
    Initial = 'Initial'
    InTableHead = 'InTableHead'
    InTableBody = 'InTableBody'
    InTableRow = 'InTableRow'
    InCompany = 'InCompany'
    InId = 'InId'
    InDate = 'InDate'


def parse_spreadsheet(spreadsheet_path):
    """Parse the spreadsheet into bios_pnp.Vendor objects."""
    tree = ElementTree.ElementTree(file=spreadsheet_path)
    root = tree.getroot()
    rows = root.findall('.//body/table/tbody/tr')
    for row in rows:
        tds = row.findall('td')
        if len(tds) == 3:
            name, pnp_id, raw_date = (elem.text.strip() for elem in tds)
            date = datetime.datetime.strptime(raw_date, '%m/%d/%Y').date()
            if len(pnp_id.encode('ascii')) != 3:
                raise ValueError('PNP ID must be exactly 3 characters')
            yield pnp.Vendor(name, pnp_id, date)


def parse_cli_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Update vendor list from a spreadsheet.')
    parser.add_argument('spreadsheet', help='path to the spreadsheet file')
    return parser.parse_args()


def generate_vendor_module(vendors):
    """Generate lines of code for vendors.py."""
    yield '# THIS FILE WAS AUTOGENERATED BY make_vendor_list.py!'
    yield '# pylint: disable=line-too-long,missing-docstring,too-many-lines'
    yield '# yapf: disable'
    yield 'import datetime'
    yield 'from bios_pnp import pnp'
    yield 'VENDORS = {'
    for vendor in vendors:
        date = 'datetime.date({}, {}, {})'.format(vendor.approval_date.year,
                                                  vendor.approval_date.month,
                                                  vendor.approval_date.day)
        key = vendor.pnp_id
        value = 'pnp.Vendor("{}", "{}", {})'.format(vendor.name, vendor.pnp_id,
                                                    date)
        line = '    "{}": {},'.format(key, value)
        yield line
    yield '}'
    yield '# yapf: enable'
    yield ''


def main():
    # pylint: disable=missing-docstring
    cli_args = parse_cli_args()

    vendors = parse_spreadsheet(cli_args.spreadsheet)

    script_path = path.abspath(path.dirname(__file__))
    output_path = path.join(script_path, 'bios_pnp', 'vendors.py')

    with open(output_path, 'w') as wfile:
        output = '\n'.join(generate_vendor_module(vendors))
        wfile.write(output)


if __name__ == '__main__':
    main()
