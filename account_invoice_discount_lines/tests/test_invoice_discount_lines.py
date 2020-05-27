# © 2017 Opener BV (<https://opener.amsterdam>)
# © 2020 Vanmoof BV (<https://www.vanmoof.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import tests
from odoo.tests.common import TransactionCase


@tests.tagged('standard', 'at_install')
class TestInvoiceDiscountLines(TransactionCase):
    def setUp(self):
        super(TestInvoiceDiscountLines, self).setUp()
        self.tax = self.env['account.tax'].create({
            'name': 'Test tax',
            'amount': 10,
            'amount_type': 'percent',
            'account_id': self.env.ref('l10n_generic_coa.1_conf_iva').id,
            'refund_account_id': self.env.ref('l10n_generic_coa.1_conf_iva').id,
        })
        product = self.env.ref('product.product_product_2')
        self.env.user.company_id.write({'discount_product': product.id})
        account = self.env.ref('l10n_generic_coa.1_conf_a_recv')
        product.write({
            'name': 'Discount',
            'property_account_income': account.id,
            'property_account_expense': account.id,
        })
        self.journal = self.env['account.journal'].search(
            [('name', '=', 'Bank')], limit=1)
        self.journal.currency_id = self.env.ref(
            'base.main_company').currency_id.id

    def create_invoice(self, price_unit=100, discount=10):
        invoice = self.env['account.invoice'].create({
            'account_id': self.env.ref('l10n_generic_coa.1_conf_a_recv').id,
            'journal_id': self.journal.id,
            'partner_id': self.env.ref('base.res_partner_12').id,
            'name': 'Test invoice',
            'invoice_line_ids': [
                (0, 0, {
                    'account_id': self.env.ref(
                        'l10n_generic_coa.1_conf_a_sale').id,
                    'name': '[PCSC234] PC Assemble SC234',
                    'price_unit': price_unit,
                    'quantity': 1,
                    'discount': discount,
                    'invoice_line_tax_ids': [(6, 0, [self.tax.id])],
                    'product_id': self.env.ref('product.product_product_3').id,
                    'uos_id': self.env.ref('uom.product_uom_unit').id,
                })],
        })
        invoice.compute_taxes()
        return invoice

    def test_01_invoice_discount_lines(self):
        self.tax.account_collected_id = False
        invoice = self.create_invoice()
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        base_line = invoice.invoice_line_ids
        self.assertTrue(
            self.env.user.company_id.currency_id.is_zero(
                invoice.amount_total - 99.00))
        self.assertEqual(base_line.discount, 10)
        self.assertEqual(base_line.discount_display, 10)
        self.assertFalse(base_line.discount_real)
        self.assertTrue(
            self.env.user.company_id.currency_id.is_zero(
                base_line.price_subtotal - 90))

        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(len(invoice.invoice_line_ids), 2)

        self.assertEqual(base_line.discount_real, 10)
        self.assertEqual(base_line.discount_display, 10)
        self.assertFalse(base_line.discount)
        self.assertTrue(
            self.env.user.company_id.currency_id.is_zero(
                base_line.price_subtotal - 100))
        self.assertTrue(
            self.env.user.company_id.currency_id.is_zero(
                invoice.amount_total - 99.0))

    def test_02_invoice_discount_lines_tax_included(self):
        self.tax.price_include = True
        self.tax.amount = .15
        invoice = self.create_invoice(50, 5)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertTrue(
            self.env.user.company_id.currency_id.is_zero(
                invoice.amount_total - 47.50))
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        self.assertTrue(
            self.env.user.company_id.currency_id.is_zero(
                invoice.amount_total - 47.50))

    def test_03_invoice_copy(self):
        invoice = self.create_invoice()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        copy = invoice.copy()[0]
        self.assertEqual(len(copy.invoice_line_ids), 1)
        self.assertTrue(
            self.env.user.company_id.currency_id.is_zero(
                invoice.amount_total - copy.amount_total))

        copy.compute_taxes()
        copy.action_invoice_open()
        self.assertEqual(copy.state, 'open')
        self.assertEqual(len(copy.invoice_line_ids), 2)
        self.assertTrue(
            self.env.user.company_id.currency_id.is_zero(
                invoice.amount_total - copy.amount_total))

    def test_04_refund(self):
        invoice = self.create_invoice()
        invoice.action_invoice_open()
        wiz = self.env['account.invoice.refund'].with_context(
            active_id=invoice.id, active_ids=[invoice.id]).create(
                {'filter_refund': 'cancel', 'description': 'reason test', })
        action = wiz.invoice_refund()
        refund_id = action['domain'][-1][-1][0]
        self.assertTrue(refund_id)
        refund = self.env['account.invoice'].browse(refund_id)
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(refund.state, 'paid')
        self.assertEqual(len(refund.invoice_line_ids), 2)
        self.assertTrue(
            self.env.user.company_id.currency_id.is_zero(
                invoice.amount_total - refund.amount_total))
