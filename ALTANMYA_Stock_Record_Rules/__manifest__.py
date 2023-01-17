# -*- coding: utf-8 -*-
###################################################################################
#
#    ALTANMYA - TECHNOLOGY SOLUTIONS
#    Copyright (C) 2022-TODAY ALTANMYA-TECHNOLOGY SOLUTIONS Part of ALTANMYA GROUP.
#    ALTANMYA - Stock Access Rights based on Locations and Operation Types.
#    Author: ALTANMYA for TECHNOLOGY (<https://tech.altanmya.net>)
#    This program is Licensed software: you can not modify
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
####################################################################################

{
    'name': 'ALTANMYA Access Rights on Warehouse, Locations and Operations',
    'version': '1.0',
    'summary': 'Users Have Access To The Warehouses and Operation Types.',
    'description': "Grant or Remove Access Rights on Warehouse, Locations and Operations",
    'category': 'Inventory/Inventory',
    'author': 'ALTANMYA - TECHNOLOGY SOLUTIONS',
    'company': 'ALTANMYA - TECHNOLOGY SOLUTIONS Part of ALTANMYA GROUP',
    'website': "https://tech.altanmya.net",
    'depends': ['stock'],
    'data': ['views/stock_location_views.xml',
             'views/stock_warehouse_views.xml',
             'views/stock_picking_type.xml',
             'security/security.xml'
             ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
