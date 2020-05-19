# © 2017 Opener BV (<https://opener.amsterdam>)
# © 2020 Vanmoof BV (<https://www.vanmoof.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Transfer discounts to separate invoice lines",
    "summary": "Keep track of discounts with journal items",
    "version": "12.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Accounting & Finance",
    "website": "https://github.com/oca/account-invoicing",
    "author": "Opener B.V.,Vanmoof B.V., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "post_init_hook": "post_init_hook",
    "data": [
        "views/account_invoice.xml",
        "views/account_invoice_line.xml",
        "views/report_invoice.xml",
        "views/res_company.xml",
    ],
    "depends": [
        "account",
    ],
    'post_init_hook': 'post_init_hook',
}
