{
    'name' : 'ZohoBook',
    'version' : '1.1',
    'summary': '',
    'sequence': -1,
    'description': """
    """,
    'category': '',
    'website': 'https://www.odoo.com/page/billing',
    'images' : ['images/accounts.jpeg','images/bank_statement.jpeg','images/cash_register.jpeg','images/chart_of_accounts.jpeg','images/customer_invoice.jpeg','images/journal_entries.jpeg'],
    'depends' : ['base', 'crm'],
    'data': [
        'views/res_company_views.xml',
        'data/authtoken_data.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
