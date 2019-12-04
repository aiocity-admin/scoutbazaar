# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re
import uuid

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat

_logger = logging.getLogger(__name__)

emails_split = re.compile(r"[;,\n\r]+")
email_validator = re.compile(r"[^@]+@[^@]+\.[^@]+")

class SelectedOptions(models.TransientModel):
    
    _inherit='survey.mail.compose.message'

    public = fields.Selection([('public_link', 'Share the public web link to your audience.'),
                            ('email_public_link', 'Send by email the public web link to your audience.'),
                            ('email_private', 'Send private invitation to your audience (only one response per recipient and per invitation).')],
                            string='Share options', default='email_private', required=True)
    

    @api.model
    def default_get(self, fields):
        rec = super(SelectedOptions, self).default_get(fields)
        # partner = self.env['event.registration'].search([])
        # states = self.env['event.registration'].sudo().search([])
        
        multi = self.env['event.registration'].search([('state', 'in', ['open'])])
        
        multi_email = ''
        for i in multi:
            multi_email += i.email + ','

        rec.update({'multi_email': multi_email})
        return rec
#harish---------------




class AttendensSurvey(models.Model):

    _inherit='event.event'

    survey_id = fields.Many2one("survey.survey", string="Survey") 

    @api.multi
    def action_send_survey(self,):
        """ Open a window to compose an email, pre-filled with the survey message """
        # Ensure that this survey has at least one page with at least one question.
        if not self.survey_id.page_ids or not [page.question_ids for page in self.survey_id.page_ids if page.question_ids]:
            raise UserError(_('You cannot send an invitation for a survey that has no questions.'))

        if self.survey_id.stage_id.closed:
            raise UserError(_("You cannot send invitations for closed surveys."))

        template = self.env.ref('survey.email_template_survey', raise_if_not_found=False)

        local_context = dict(
            self.env.context,
            default_model='survey.survey',
            default_res_id=self.survey_id.id,
            default_survey_id=self.survey_id.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            notif_layout='mail.mail_notification_light',
        )
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'survey.mail.compose.message',
            'target': 'new',
            'context': local_context,
        }