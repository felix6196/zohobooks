from odoo import fields, models, api, tools, _
from odoo.exceptions import ValidationError
import base64
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
import requests
import json
import logging

_logger = logging.getLogger(__name__)
class Lead(models.Model):
    _inherit = 'crm.lead'

    zoho_id = fields.Char("Zoho ID")
    is_zoho = fields.Boolean("Zoho ?")
    
    @api.model
    def create(self, vals):
        company_id = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
        token= company_id.access_token
        # token = "1000.8c08c0ce78c866eb8e14e6dc8dc15c39.8cd8ca071b2b656222d4282e207fc808"
        #need to change is_zoho = True
        headers = {"Authorization":"Zoho-oauthtoken "+token,"Content-Type":"application/json"}
        url = "https://www.zohoapis.com/crm/v2/Leads"
        data_list = []
        params = {}
        if not vals.get('zoho_id'):
            params['id'] = vals.get('zoho_id')
            # params['Company'] = vals.get('parent_id')
            params['Last_Name'] = vals.get('name')
            if vals.get('phone'):
                params['Phone'] = vals.get('phone')
            if vals.get('email_from'):
                params['Email'] = vals.get('email_from')
            # params['Website'] = vals.get('website')
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
        return super(Lead, self).create(vals)
    
    @api.multi
    def write(self, vals):
        company_id = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
        token= company_id.access_token
        # token = "1000.8c08c0ce78c866eb8e14e6dc8dc15c39.8cd8ca071b2b656222d4282e207fc808"
        #need to change is_zoho = True
        headers = {"Authorization":"Zoho-oauthtoken "+token,"Content-Type":"application/json"}
        url = "https://www.zohoapis.com/crm/v2/Leads"
        data_list = []
        params = {}
        params['id'] = self.zoho_id
        # params['Company'] = vals.get('parent_id')
        if vals.get('name'):
            params['Last_Name'] = vals.get('name')
        else:
            params['Last_Name'] = self.name
        if vals.get('phone'):
            params['Phone'] = vals.get('phone')
        if vals.get('email_from'):
            params['Email'] = vals.get('email_from')
        data_list.append(params)
        data_map = {}
        data_map['data'] = data_list
        payload = json.dumps(data_map)
        # payload = 'JSONString={"Last_Name":%s,"Full_Name":"%s","Company":"%s"}' %(contact.name,contact.name,contact.company_id.name)
        if vals.get('name'):
            response = requests.put(url,headers=headers,data=payload)
            if response.status_code == 200:
                decoded = json.loads(response.text)
                print(decoded)
                contact_datas = decoded.get('data')
                for contact in contact_datas:
                    contact_id = contact['details']['id']
                    vals.update({'zoho_id': contact_id})
        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            vals['date_last_stage_update'] = fields.Datetime.now()
        if vals.get('user_id') and 'date_open' not in vals:
            vals['date_open'] = fields.Datetime.now()
        # stage change with new stage: update probability and date_closed
        if vals.get('stage_id') and 'probability' not in vals:
            vals.update(self._onchange_stage_id_values(vals.get('stage_id')))
        if vals.get('probability', 0) >= 100 or not vals.get('active', True):
            vals['date_closed'] = fields.Datetime.now()
        elif 'probability' in vals:
            vals['date_closed'] = False
        return super(Lead, self).write(vals)