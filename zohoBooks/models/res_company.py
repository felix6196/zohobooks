from odoo import fields, models, api, tools, _
from odoo.exceptions import ValidationError
import base64
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
import requests
import json
import logging

_logger = logging.getLogger(__name__)
    
class ResCompany(models.Model):
    _inherit = "res.company"
    _order = "name asc"

    data_center = fields.Selection([('com', 'COM'),('in', 'IN'),('eu', 'EU'),('com.au', 'COM.AU')],default='com',string='Data Center')
    client_id = fields.Char('Client ID')
    client_secret = fields.Char('Client Secret')
    redirect_url = fields.Char('Redirect URL')
    refresh_token = fields.Char('Refresh Token')
    access_token = fields.Char('Access Token')
    Organization_id = fields.Char('Organization ID')
    
    @api.model
    def _generate_authtoken_cron(self):
        l = 10
        for i in range(0, l):
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.generate_authtoken()
    @api.multi
    def generate_authtoken(self):
        company_id = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
        refresh_token = company_id.refresh_token
        client_id =  company_id.client_id
        client_secret =  company_id.client_secret
        # refresh_token ="1000.766f3117c2f5d417442fe82757eb2421.d189bf8f1434ef206ba5c93923824cf0" #company_id.refresh_token
        # client_id = "1000.CFHT8LCRJ47K90NP8434LPYN4C8FJO"#company_id.client_id
        # client_secret = "a014770a9b0c4a60e4dc64455df00bfaeb61bdd824"#company_id.client_secret
        redirect_uri = "https://www.zoho.com"
        headers = {"Content-Type":"application/x-www-form-urlencoded"}
        url = "https://accounts.zoho.com/oauth/v2/token?refresh_token=%s&client_id=%s&client_secret=%s&redirect_uri=%s&grant_type=refresh_token"%(refresh_token,client_id,client_secret,redirect_uri)
        response = requests.post(url,headers=headers)
        if response.status_code == 200:
            decoded = json.loads(response.text)
            final_auth_token = decoded['access_token']
            print(final_auth_token)
            company_id.sudo().write({'access_token':final_auth_token})
    
    def check_conf(self):
        if not self.client_id:
            raise ValidationError("Please configure the Client ID")
        if not self.client_secret:
            raise ValidationError("Please configure the Client Secret")
        if not self.refresh_token:
            raise ValidationError("Please configure the Refresh Token")
        if not self.access_token:
            raise ValidationError("Please configure the Access Token")
    
    @api.multi                
    def import_leads(self):
        token= self.access_token
        #need to change is_zoho = True
        contacts = self.env['crm.lead'].search(['&',('is_zoho','=',False),('zoho_id','=',False)])
        for contact in contacts:
            headers = {"Authorization":"Zoho-oauthtoken "+token,"Content-Type":"application/json"}
            url = "https://www.zohoapis.com/crm/v2/Leads"
            data_list = []
            params = {}
            params['id'] = contact.zoho_id
            # params['Company'] = vals.get('parent_id')
            params['Last_Name'] = contact.name
            if contact.phone:
                params['Phone'] = contact.phone
            if contact.email_from:
                params['Email'] = contact.email_from
            data_list.append(params)
            data_map = {}
            data_map['data'] = data_list
            payload = json.dumps(data_map)
            # payload = 'JSONString={"Last_Name":%s,"Full_Name":"%s","Company":"%s"}' %(contact.name,contact.name,contact.company_id.name)
            response = requests.post(url,headers=headers,data=payload)
            decoded = json.loads(response.text)
            print(decoded)
            contact_datas = decoded.get('data')
            for contact_dict in contact_datas:
                contact_id = contact_dict['details']['id']
                contact.write({'zoho_id': contact_id})
    
    @api.multi
    def export_leads(self):
        self.check_conf()
        token= self.access_token
        headers = {"Authorization":"Zoho-oauthtoken "+token,"Content-Type":"application/json"}
        url = "https://www.zohoapis.com/crm/v2/Leads"
        response = requests.get(url, headers=headers)
        decoded = json.loads(response.text)
        # _logger.error(response.text)
        if response.status_code == 200:
            decoded = json.loads(response.text)
            contacts = decoded.get('data')
            # print(contacts)
            len(contacts)
            for contact in contacts:
                zoho_lead_id = contact.get('id')
                check_contact = self.env['crm.lead'].search([('zoho_id','=',zoho_lead_id)])
                if not check_contact:
                    vals = {}
                    vals['name'] = contact.get('Full_Name')
                    vals['zoho_id'] = zoho_lead_id
                    vals['is_zoho'] = True
                    vals['active'] = True
                    vals['email_from'] = contact.get('Email')
                    vals['phone'] = contact.get('Phone')
                    create_contact = self.env['crm.lead'].create(vals)
                    if create_contact:
                        _logger.error("Lead Created : "+str(create_contact.id))

                else:
                    vals = {}
                    vals['name'] = contact.get('Full_Name')
                    vals['zoho_id'] = zoho_lead_id
                    vals['is_zoho'] = True
                    vals['active'] = True
                    vals['email_from'] = contact.get('Email')
                    vals['phone'] = contact.get('Phone')
                    create_contact = self.env['crm.lead'].write(vals)
                    check_contact.write(vals)
                    _logger.error("Lead Updated ")
    
    @api.multi
    def import_contacts(self):
        token= self.access_token
        #need to change is_zoho = True
        contacts = self.env['res.partner'].search(['&',('is_zoho','=',False),('zoho_id','=',False)])
        for contact in contacts:
            headers = {"Authorization":"Zoho-oauthtoken "+token,"Content-Type":"application/json"}
            url = "https://www.zohoapis.com/crm/v2/Contacts"
            data_list = []
            params = {}
            params['id'] = contact.zoho_id
            # params['Company'] = vals.get('parent_id')
            params['Last_Name'] = contact.name
            if contact.phone:
                params['Phone'] = contact.phone
            if contact.email:
                params['Email'] = contact.email
            if contact.mobile:
                params['Mobile'] = contact.mobile
            if contact.website:
                params['Website'] = contact.website
            data_list.append(params)
            data_map = {}
            data_map['data'] = data_list
            payload = json.dumps(data_map)
            # payload = 'JSONString={"Last_Name":%s,"Full_Name":"%s","Company":"%s"}' %(contact.name,contact.name,contact.company_id.name)
            response = requests.post(url,headers=headers,data=payload)
            decoded = json.loads(response.text)
            print(decoded)
            if response.status_code == 200:
                contact_datas = decoded.get('data')
                for contact_dict in contact_datas:
                    contact_id = contact_dict['details']['id']
                    contact.write({'zoho_id': contact_id, 'is_zoho': True})
    
    @api.multi
    def export_contacts(self):
        self.check_conf()
        token= self.access_token
        headers = {"Authorization":"Zoho-oauthtoken "+token,"Content-Type":"application/json"}
        url = "https://www.zohoapis.com/crm/v2/Contacts"
        response = requests.get(url, headers=headers)
        decoded = json.loads(response.text)
        # _logger.error(response.text)
        if response.status_code == 200:
            decoded = json.loads(response.text)
            contacts = decoded.get('data')
            # print(contacts)
            len(contacts)
            for contact in contacts:
                zoho_lead_id = contact.get('id')
                check_contact = self.env['res.partner'].search(['&',('is_zoho','=',False),('zoho_id','=',False)])
                if not check_contact:
                    vals = {}
                    vals['name'] = contact.get('Full_Name')
                    vals['zoho_id'] = zoho_lead_id
                    vals['is_zoho'] = True
                    vals['active'] = True
                    vals['email'] = contact.get('Email')
                    vals['phone'] = contact.get('Phone')
                    vals['mobile'] = contact.get('Mobile')
                    vals['website'] = contact.get('Website')
                    create_contact = self.env['res.partner'].create(vals)
                    if create_contact:
                        _logger.error("Contact Created : "+str(create_contact.id))

                else:
                    vals = {}
                    vals['name'] = contact.get('Full_Name')
                    vals['zoho_id'] = zoho_lead_id
                    vals['is_zoho'] = True
                    vals['active'] = True
                    vals['email'] = contact.get('Email')
                    vals['phone'] = contact.get('Phone')
                    vals['mobile'] = contact.get('Mobile')
                    vals['website'] = contact.get('Website')
                    create_contact = self.env['res.partner'].write(vals)
                    check_contact.write(vals)
                    _logger.error("Contact Updated ")
    
