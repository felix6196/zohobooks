from odoo import fields, models, api, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
import base64
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = 'res.partner'

    zoho_id = fields.Char("Zoho ID")
    is_zoho = fields.Boolean("Zoho ?")
    
    @api.model
    def create(self, vals):
        company_id = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
        token= company_id.access_token
        # token = "1000.1f287230fb2fe188b932600eb8060b9c.2df00d8d94c8c95b1633c102c34b7470"
        #need to change is_zoho = True
        headers = {"Authorization":"Zoho-oauthtoken "+token,"Content-Type":"application/json"}
        url = "https://www.zohoapis.com/crm/v2/Contacts"
        data_list = []
        params = {}
        if not vals.get('zoho_id'):
            params['id'] = vals.get('zoho_id')
            # params['Company'] = vals.get('parent_id')
            params['Last_Name'] = vals.get('name')
            if vals.get('phone'):
                params['Phone'] = vals.get('phone') 
            if vals.get('email'):
                params['Email'] = vals.get('email')
            if vals.get('mobile'):
                params['Mobile'] = vals.get('mobile')
            if vals.get('website'):
                params['Website'] = vals.get('website')
            data_list.append(params)
            data_map = {}
            data_map['data'] = data_list
            payload = json.dumps(data_map)
            # payload = 'JSONString={"Last_Name":%s,"Full_Name":"%s","Company":"%s"}' %(contact.name,contact.name,contact.company_id.name)
            response = requests.post(url,headers=headers,data=payload)
            decoded = json.loads(response.text)
            print(decoded)
            contact_datas = decoded.get('data')
            for contact in contact_datas:
                contact_id = contact['details']['id']
                vals.update({'zoho_id': contact_id})
        return super(Partner, self).create(vals)
    
    @api.multi
    def write(self, vals):
        company_id = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
        token= company_id.access_token
        # token = "1000.1f287230fb2fe188b932600eb8060b9c.2df00d8d94c8c95b1633c102c34b7470"
        #need to change is_zoho = True
        headers = {"Authorization":"Zoho-oauthtoken "+token,"Content-Type":"application/json"}
        url = "https://www.zohoapis.com/crm/v2/Contacts"
        data_list = []
        params = {}
        if vals.get('zoho_id'):
            params['id'] = vals.get('zoho_id')
        # params['Company'] = vals.get('parent_id')
        if vals.get('name'):
            params['Last_Name'] = vals.get('name')
        else:
            params['Last_Name'] = self.name
        if vals.get('phone'):
            params['Phone'] = vals.get('phone') 
        if vals.get('email'):
            params['Email'] = vals.get('email')
        if vals.get('mobile'):
            params['Mobile'] = vals.get('mobile')
        if vals.get('website'):
            params['Website'] = vals.get('website')
        data_list.append(params)
        data_map = {}
        data_map['data'] = data_list
        payload = json.dumps(data_map)
        # payload = 'JSONString={"Last_Name":%s,"Full_Name":"%s","Company":"%s"}' %(contact.name,contact.name,contact.company_id.name)
        if vals.get('name') or vals.get('phone') or vals.get('email') or vals.get('mobile') or vals.get('website'):
            response = requests.put(url,headers=headers,data=payload)
            if response.status_code == 201:
                decoded = json.loads(response.text)
                print(decoded)
                contact_datas = decoded.get('data')
                for contact in contact_datas:
                    contact_id = contact['details']['id']
                    vals.update({'zoho_id': contact_id})
        # res.partner must only allow to set the company_id of a partner if it
        # is the same as the company of all users that inherit from this partner
        # (this is to allow the code from res_users to write to the partner!) or
        # if setting the company_id to False (this is compatible with any user
        # company)
        if vals.get('website'):
            vals['website'] = self._clean_website(vals['website'])
        if vals.get('parent_id'):
            vals['company_name'] = False
        if vals.get('company_id'):
            company = self.env['res.company'].browse(vals['company_id'])
            for partner in self:
                if partner.user_ids:
                    companies = set(user.company_id for user in partner.user_ids)
                    if len(companies) > 1 or company not in companies:
                        raise UserError(_("You can not change the company as the partner/user has multiple user linked with different companies."))
        tools.image_resize_images(vals)

        result = True
        # To write in SUPERUSER on field is_company and avoid access rights problems.
        if 'is_company' in vals and self.user_has_groups('base.group_partner_manager') and not self.env.uid == SUPERUSER_ID:
            result = super(Partner, self.sudo()).write({'is_company': vals.get('is_company')})
            del vals['is_company']
        result = result and super(Partner, self).write(vals)
        for partner in self:
            if any(u.has_group('base.group_user') for u in partner.user_ids if u != self.env.user):
                self.env['res.users'].check_access_rights('write')
            partner._fields_sync(vals)
        return result


