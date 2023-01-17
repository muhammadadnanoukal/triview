# -*- coding: utf-8 -*-
###################################################################################
#
#    ALTANMYA - TECHNOLOGY SOLUTIONS
#    Copyright (C) 2022-TODAY ALTANMYA-TECHNOLOGY SOLUTIONS Part of ALTANMYA GROUP.
#    ALTANMYA - Stock Report Extension-L1.
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
    'name': 'ALTANMYA Stock Report Extension-L1',
    'version': '1.0',
    'summary': 'A Dynamic report for each product, type of transaction, and transaction with retrospective effects',
    'description': "A Dynamic report that shows both beginning balance and ending balance for each product, type of transaction, and transaction with retrospective effects",
    'category': 'Inventory/Inventory',
    'author': 'ALTANMYA - TECHNOLOGY SOLUTIONS',
    'company': 'ALTANMYA - TECHNOLOGY SOLUTIONS Part of ALTANMYA GROUP',
    'website': "http://tech.altanmya.net",
    'depends': ['stock', 'product'],
    'data': ['security/ir.model.access.csv',
             'security/sec.xml',
             'views/view_pages.xml'],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
