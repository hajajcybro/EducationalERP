# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjana P V(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import base64
from odoo import http
from odoo.http import request


class OnlineAdmission(http.Controller):
    """Controller for taking online admission"""

    @http.route('/admission/form/submit', type='http', auth="public",
                website=True, csrf=True)
    def eadm_submit(self, **kwargs):
        guardian = request.env['res.partner'].sudo().create({
                        'name': kwargs.get('father'),
                        'is_parent': True
                    })

        binary_image = base64.b64encode((kwargs.get('image')).read())
        application = request.env['education.application'].sudo().create({
            'first_name': kwargs.get('name'),
            'last_name': kwargs.get('last_name'),
            'mother_name': kwargs.get('mother'),
            'father_name': kwargs.get('father'),
            'mobile': kwargs.get('phone'),
            'email': kwargs.get('email'),
            'date_of_birth': kwargs.get('date'),
            'academic_year_id': kwargs.get('academic_year'),
            'mother_tongue': kwargs.get('tongue'),
            'medium_id': kwargs.get('medium'),
            'sec_lang_id': kwargs.get('sec_lang'),
            'admission_class_id': kwargs.get('classes'),
            'street': kwargs.get('communication_address'),
            'per_street': kwargs.get('communication_address'),
            'blood_group': kwargs.get('blood_group'),
            'gender': kwargs.get('gender'),
            'guardian_id': guardian.id,
            'image': binary_image
        })
        attachment = request.env['ir.attachment'].sudo().create({
            'name': kwargs.get('document_attachment').filename,
            'type': 'binary',
            'datas': base64.b64encode(
                (kwargs.get('document_attachment')).read()),
        })
        request.env['education.document'].sudo().create({
            'application_ref_id': application.id,
            'document_type_id': kwargs.get('doc_type'),
            'doc_attachment_ids': [(4, attachment.id)],
        })
        return request.render(
            "education_student_portal.submit_admission",
            {})

    @http.route('/online_admission', type='http', auth='public', website=True)
    def online_admission(self):
        """To pass certain default field values to the website registration
        form."""
        vals = {
            'class': request.env['education.class'].sudo().search([]),
            'year': request.env['education.academic.year'].sudo().search([]),
            'medium': request.env['education.medium'].sudo().search([]),
            'sec_lang': request.env['education.subject'].sudo().search([]),
            'doc_type': request.env['document.document'].sudo().search([])
        }
        return request.render('education_student_portal.online_admission', vals)
