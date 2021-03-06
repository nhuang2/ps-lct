# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 OpenERP (<openerp@openerp-HP-ProBook-430-G1>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from xlrd import open_workbook,XL_CELL_BLANK
from xlutils.copy import copy
import StringIO
import base64
from datetime import datetime
import os
from openerp.exceptions import Warning

class balance_sheet(osv.osv_memory):

    _inherit = "accounting.report"
    _name = "lct_finance.balance.sheet"
    def _getOutCell(self,outSheet, colIndex, rowIndex):
        row = outSheet._Worksheet__rows.get(rowIndex)
        if not row: return None
        cell = row._Row__cells.get(colIndex)
        return cell

    def _setOutCell(self,outSheet, col, row, value):
        previousCell = self._getOutCell(outSheet, col, row)
        outSheet.write(row, col, value)
        if previousCell:
            newCell = self._getOutCell(outSheet, col, row)
            if newCell:
                newCell.xf_idx = previousCell.xf_idx


    def _write_report(self, cr, uid, ids, context=None):
        module_path = __file__.split('wizard')[0]
        xls_file = os.path.join(module_path, 'data', 'balancesheet.xls')
        template = open_workbook(xls_file, formatting_info=True)
        report = copy(template)
        ts = template.sheet_by_index(0)
        rs = report.get_sheet(0)
        acc_ids = []
        rows = []
        for row in range(10,ts.nrows) :
            if ts.cell(row,1).ctype != XL_CELL_BLANK :
                domain = [('code','ilike',str(ts.cell(row,1).value))]
                if not self.pool.get('account.account').search(cr, uid, domain,context=context) :
                    continue
                acc_id = self.pool.get('account.account').search(cr, uid, domain,context=context)[0]
                acc_ids.append(acc_id)
                rows.append(row)

        browser = self.browse(cr,uid,ids,context=context)[0]
        today_s = datetime.today().strftime("%d-%m-%Y")
        date_from = None
        date_to = None

        if browser.filter == 'filter_date':
            if not (browser.date_from and browser.date_to):
                raise Warning('You need to specify a start date and an end date')
            context['date_from'] = date_from = browser.date_from
            context['date_to'] = date_to = browser.date_to

        if browser.filter == 'filter_period':
            if not (browser.period_from and browser.period_to):
                raise Warning('You need to specify a start period and an end period')
            context['period_from'] = browser.period_from.id
            context['period_to'] = browser.period_to.id
            date_from = browser.period_from.date_start
            date_to = browser.period_to.date_stop

        else :
            self._setOutCell(rs, 1, 7, "Date of report :")
            self._setOutCell(rs, 2, 7, today_s)

        context['state'] = 'posted'
        if date_from and date_to:
            self._setOutCell(rs, 1, 7, "Start date :")
            self._setOutCell(rs, 1, 8, "End date :")
            self._setOutCell(rs, 2, 7, datetime.strptime(date_from, "%Y-%m-%d").strftime("%d-%m-%Y"))
            self._setOutCell(rs, 2, 8, datetime.strptime(date_to, "%Y-%m-%d").strftime("%d-%m-%Y"))
            self._setOutCell(rs, 1, 6, "Date of report :")
            self._setOutCell(rs, 2, 6, today_s)

        accounts = self.pool.get('account.account').browse(cr,uid,acc_ids,context=context)
        for row in rows :
            col = 3
            balance = accounts[rows.index(row)].balance
            if balance !=0 : self._setOutCell(rs, col, row, balance)
            else : self._setOutCell(rs, col, row, "")
        return report


    def print_report(self, cr, uid, ids, name, context=None):
        if context is None:
            context = {}
        report = self._write_report(cr,uid,ids,context=context)

        f = StringIO.StringIO()
        report.save(f)
        xls_file = base64.b64encode(f.getvalue())
        dlwizard = self.pool.get('lct_finance.file.download').create(cr, uid, {'file' : xls_file, 'file_name' : 'Balance sheet.xls'}, context=dict(context, active_ids=ids))
        return {
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'lct_finance.file.download',
            'res_id': dlwizard,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': dict(context, active_ids=ids)
        }

