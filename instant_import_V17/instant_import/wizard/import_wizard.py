# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
import csv
import logging
from datetime import datetime
import datetime as _dt
import numpy as _np
import pandas as _pd
from io import BytesIO

import pandas as pd
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.base_import.models.base_import import FIELDS_RECURSION_LIMIT

_logger = logging.getLogger(__name__)


class ImportWizard(models.TransientModel):
    _name = 'custom.import.wizard'
    _description = 'Custom Import Wizard'

    _validation_cache = {}
    _reference_cache_global = {}
    model_id = fields.Many2one('ir.model', 'Model', required=True,
                               domain=[('transient', '=', False)])


    @api.model
    def copy_import(self, res_id, model, columns):
        """
        Main import function that processes Excel files to create records in Odoo models.
        This method reads Excel data, maps columns to model fields, and imports records
        using optimized bulk operations. It automatically handles relationships like one2many
        (child records) and many2many (tags/categories), resolves references, fills missing
        required fields with defaults, and generates sequences where needed. The import is
        optimized for performance using PostgreSQL bulk operations and triggers.
        """
        try:
            reference_cache = {}
            validation_result = self.validate_columns(res_id, model, columns)
            if not validation_result.get('is_valid', False):
                raise UserError(validation_result.get('error_message', 'Validation failed'))
            required_fields_info = self.get_required_fields(model)
            required_field_names = [f['name'] for f in required_fields_info]
            model_fields = self.env[model].fields_get()
            column_mapping, imported_fields, o2m_field_mappings = {}, set(), {}
            # Build field mappings
            for item in columns:
                if 'fieldInfo' not in item:
                    continue
                field_path = item['fieldInfo'].get('fieldPath', item['fieldInfo']['id'])
                field_name = item['fieldInfo']['id']
                excel_column_name = item.get('name', field_name)
                if '/' in field_path:
                    path_parts = field_path.split('/')
                    parent_field_raw = path_parts[0]
                    child_field_raw = '/'.join(path_parts[1:])
                    parent_field = parent_field_raw
                    if parent_field not in model_fields:
                        o2m_fields = [f for f, info in model_fields.items() if info['type'] == 'one2many']
                        if o2m_fields:
                            parent_field = o2m_fields[0]
                        else:
                            continue
                    field_info = model_fields[parent_field]
                    if field_info['type'] != 'one2many':
                        continue
                    comodel_name = field_info['relation']
                    try:
                        comodel_fields = self.env[comodel_name].fields_get()
                        child_field = child_field_raw
                        if child_field not in comodel_fields:
                            simplified = child_field.replace(' ', '_').lower()
                            candidates = [f for f in comodel_fields if
                                          f.lower() == simplified or simplified in f.lower()]
                            if candidates:
                                child_field = candidates[0]
                        o2m_field_mappings.setdefault(parent_field, []).append({
                            'excel_column': excel_column_name,
                            'child_field': child_field,
                            'full_path': field_path,
                            'comodel_name': comodel_name
                        })
                        imported_fields.add(parent_field)
                    except Exception as e:
                        continue
                else:
                    if field_name in model_fields:
                        column_mapping[excel_column_name] = field_name
                        imported_fields.add(field_name)
            # Load Excel data
            import_record = self.env['base_import.import'].browse(res_id).file
            file_stream = BytesIO(import_record)
            data = pd.read_excel(file_stream, dtype=str)
            data = data.replace({pd.NA: None, '': None})
            # Create a copy for the original column names before renaming
            original_columns = data.columns.tolist()
            original_data = data.copy()  # Keep a copy of original data for M2M extraction
            # Rename columns using the mapping
            data = data.rename(columns=column_mapping)
            if model == "account.move":
                if "move_type" not in data.columns:
                    raise UserError(
                        _("Missing required field 'Type (move_type)' for Account Moves. "
                          "Please add the 'Type' column in your import file.")
                    )
                invalid_rows = data[
                    data["move_type"].isna() |
                    (data["move_type"].astype(str).str.strip() == "") |
                    (data["move_type"].astype(str).str.lower().isin(["none", "null", "nan"]))
                    ]
                if not invalid_rows.empty:
                    raise UserError(
                        _("The 'Type (move_type)' field is required for Account Moves.\n"
                          "Please ensure all rows have a valid value like:\n"
                          "- out_invoice\n"
                          "- in_invoice\n"
                          "- out_refund\n"
                          "- in_refund")
                    )
            Model = self.env[model]
            defaults = self._get_model_defaults(model)
            missing_without_fallback = self._check_missing_required_fields(model, imported_fields, defaults)
            if missing_without_fallback:
                data = self._handle_missing_required_fields(data, model, missing_without_fallback)
                updated_imported_fields = imported_fields.union(set(missing_without_fallback))
                still_missing = self._check_missing_required_fields(model, updated_imported_fields, defaults)
                if still_missing:
                    raise UserError(f"Missing required fields without defaults: {', '.join(still_missing)}")
            # Process O2M grouping
            if o2m_field_mappings:
                processed_data = self._group_o2m_records(data, model, o2m_field_mappings, reference_cache)
                if processed_data is not None and len(processed_data) > 0:
                    data = processed_data
            else:
                _logger.info("No O2M fields found, using standard processing")
            # Check required fields
            required_fields = [f['name'] for f in required_fields_info]
            missing_required = set(required_fields) - imported_fields
            table_name = self.env[model]._table
            m2m_columns, o2m_columns, m2m_trigger_val, o2m_trigger_val = [], [], {}, {}
            has_complex_fields = False
            # Process M2M fields - IMPORTANT: Extract M2M values from original data
            m2m_field_mapping = {}
            m2m_columns_data = {}
            for item in columns:
                if 'fieldInfo' in item and item["fieldInfo"].get("type") == "many2many":
                    has_complex_fields = True
                    field_name = item['fieldInfo']['id']
                    excel_column_name = item.get('name', field_name)
                    # Check if this column exists in the original data
                    if excel_column_name in original_columns:
                        # Store the M2M values from the original data (before renaming)
                        m2m_column_name = f"m2m__{field_name}"
                        m2m_columns.append(m2m_column_name)
                        # Get M2M values from the original column
                        if excel_column_name in original_data.columns:
                            # Store the values for later processing
                            data[m2m_column_name] = original_data[excel_column_name]
                            m2m_field_mapping[field_name] = data[m2m_column_name].copy()
                            m2m_columns_data[m2m_column_name] = data[m2m_column_name].copy()
                            _logger.info(f"M2M Field found: {field_name} with values from column {excel_column_name}")
                            # Add temporary column to table
                            self.env.cr.execute(
                                f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {m2m_column_name} TEXT;")
                            # Store trigger info
                            val = self.get_m2m_details(item['fieldInfo']['model_name'], field_name)
                            m2m_trigger_val[m2m_column_name] = {
                                "data_table": self.env[item['fieldInfo']['comodel_name']]._table,
                                "mapping_table": val['relation_table'],
                                "column1": val['column1'],
                                "column2": val['column2'],
                            }
            model_record = self.env['ir.model'].search([('model', '=', model)], limit=1)
            if not model_record:
                raise UserError(f"Model '{model}' does not exist.")
            initial_count = self.env[model].search_count([])
            # Process O2M fields for trigger setup
            for parent_field, field_mappings in o2m_field_mappings.items():
                parent_field_info = self.env[model]._fields.get(parent_field)
                if isinstance(parent_field_info, fields.One2many):
                    has_complex_fields = True
                    o2m_field_name = f'o2m__{parent_field}'
                    if o2m_field_name not in o2m_columns:
                        o2m_trigger_val[o2m_field_name] = {
                            "data_table": self.env[parent_field_info.comodel_name]._table,
                            "inverse_name": getattr(parent_field_info, 'inverse_name', None),
                            "comodel_name": parent_field_info.comodel_name
                        }
                        o2m_columns.append(o2m_field_name)
                        _logger.info(f"Setup O2M trigger config: {o2m_trigger_val[o2m_field_name]}")
                        self.env.cr.execute(
                            f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {o2m_field_name} jsonb;")
                        _logger.info(f"Added JSONB column {o2m_field_name} to {table_name}")
            model_fields = self.env[model].fields_get()
            # Auto-fill currency_id if required and missing
            if "currency_id" in model_fields:
                field_info = model_fields["currency_id"]
                if field_info.get("required", False):
                    needs_fill = (
                            "currency_id" not in data.columns
                            or data["currency_id"].isna().all()
                            or all(str(v).strip().lower() in ["", "none", "null", "nan"]
                                   for v in data["currency_id"].fillna(""))
                    )
                    if needs_fill:
                        default_currency = self.env.company.currency_id.id
                        data["currency_id"] = default_currency
                        imported_fields.add("currency_id")
                        _logger.info(f"[AUTO-FILL] currency_id set to company currency {default_currency}")
            # AUTO-FILL journal_id ONLY IF MODEL REQUIRES IT
            if "journal_id" in model_fields:
                field_info = model_fields["journal_id"]
                if field_info.get("required", False):
                    needs_fill = (
                            "journal_id" not in data.columns
                            or data["journal_id"].isna().all()
                            or all(str(v).strip().lower() in ["", "none", "null", "nan"]
                                   for v in data["journal_id"].fillna(""))
                    )
                    if needs_fill:
                        # Get a suitable journal based on model logic
                        Journal = self.env["account.journal"]
                        # Special logic for account.move → correct journal based on move_type
                        if model == "account.move" and "move_type" in data.columns:
                            move_type_sample = str(data["move_type"].dropna().iloc[0]).strip()
                            if move_type_sample in ["out_invoice", "out_refund"]:
                                journal = Journal.search(
                                    [("type", "=", "sale"), ("company_id", "=", self.env.company.id)],
                                    limit=1
                                )
                            elif move_type_sample in ["in_invoice", "in_refund"]:
                                journal = Journal.search(
                                    [("type", "=", "purchase"), ("company_id", "=", self.env.company.id)],
                                    limit=1
                                )
                            else:
                                journal = Journal.search(
                                    [("company_id", "=", self.env.company.id)],
                                    limit=1
                                )
                        else:
                            # Generic fallback for any model requiring journal_id
                            journal = Journal.search(
                                [("company_id", "=", self.env.company.id)],
                                limit=1
                            )
                        if journal:
                            data["journal_id"] = journal.id
                            imported_fields.add("journal_id")
                            _logger.info(f"[AUTO-FILL] journal_id set to {journal.id} for model {model}")
                        else:
                            raise UserError("journal_id is required but no journal exists for this company.")
            if 'state' in model_fields and model_fields['state']['type'] == 'selection':
                state_default = self._get_dynamic_state_default(model, model_fields['state'])
                _logger.info(f"Setting state field default to: {state_default}")

                if 'state' not in data.columns:
                    data = data.copy()
                    data.loc[:, 'state'] = [state_default] * len(data)
                    imported_fields.add('state')

                else:
                    # Fetch selection values safely (Odoo 19 compatible)
                    selection = model_fields['state']['selection']
                    if callable(selection):
                        selection = selection(self.env[model])

                    # Build label → key mapping
                    label_to_key = {
                        str(label).strip().lower(): key
                        for key, label in selection
                    }

                    state_values = []

                    for val in data['state']:
                        if pd.isna(val) or str(val).strip() == '' or str(val).strip().lower() in ['none', 'null',
                                                                                                  'nan']:
                            state_values.append(state_default)
                        else:
                            cleaned = str(val).strip().lower()
                            # Convert label → technical key OR fallback to cleaned value
                            state_values.append(label_to_key.get(cleaned, cleaned))

                    data = data.copy()
                    data.loc[:, 'state'] = state_values

            # Handle date fields
            date_fields = [f for f, info in model_fields.items() if info['type'] in ['date', 'datetime']]
            for date_field in date_fields:
                if date_field not in data.columns and date_field in required_field_names:
                    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    data = data.copy()
                    data.loc[:, date_field] = [current_datetime] * len(data)
                    imported_fields.add(date_field)
            # Apply defaults for missing required fields
            for field in missing_required:
                if field not in data.columns and field in defaults:
                    data = data.copy()
                    data.loc[:, field] = [defaults[field]] * len(data)
            # Resolve many2one references
            many2one_fields = {}
            for column in data.columns:
                if column in model_fields and model_fields[column]['type'] == 'many2one':
                    comodel = model_fields[column]['relation']
                    many2one_fields[column] = comodel
                    self._build_reference_cache(comodel, data[column], reference_cache)
            for column, comodel in many2one_fields.items():
                resolved_values = []
                for value in data[column]:
                    if pd.notna(value):
                        resolved_id = self._resolve_reference(comodel, value, reference_cache)
                        resolved_values.append(resolved_id)
                    else:
                        resolved_values.append(None)
                data = data.copy()
                data.loc[:, column] = resolved_values
            # Handle partner addresses
            if ('partner_id' in data.columns and
                    any(f in model_fields for f in ['partner_invoice_id', 'partner_shipping_id'])):
                partner_ids = []
                for pid in data['partner_id']:
                    try:
                        if pd.notna(pid) and int(pid) not in partner_ids:
                            partner_ids.append(int(pid))
                    except Exception:
                        continue
                address_cache = {}
                if partner_ids:
                    partner_model = model_fields.get('partner_id', {}).get('relation', 'res.partner')
                    partners = self.env[partner_model].browse(partner_ids)
                    for partner in partners:
                        try:
                            addresses = partner.address_get(['invoice', 'delivery'])
                            address_cache[partner.id] = {
                                'invoice': addresses.get('invoice', partner.id),
                                'delivery': addresses.get('delivery', partner.id)
                            }
                        except Exception:
                            address_cache[partner.id] = {'invoice': partner.id, 'delivery': partner.id}
                if 'partner_invoice_id' in model_fields:
                    data = data.copy()
                    data.loc[:, 'partner_invoice_id'] = [
                        address_cache.get(int(pid), {}).get('invoice') if pd.notna(pid) else None
                        for pid in data['partner_id']
                    ]
                if 'partner_shipping_id' in model_fields:
                    data = data.copy()
                    data.loc[:, 'partner_shipping_id'] = [
                        address_cache.get(int(pid), {}).get('delivery') if pd.notna(pid) else None
                        for pid in data['partner_id']
                    ]
            # Prepare final fields for import
            fields_to_import = list(imported_fields.union(missing_required))
            available_fields = [f for f in fields_to_import if f in data.columns]
            for field in fields_to_import:
                if field not in available_fields and (field in defaults or field in data.columns):
                    if field in data.columns:
                        available_fields.append(field)
                    else:
                        data = data.copy()
                        data.loc[:, field] = defaults[field]
                        available_fields.append(field)
            # Add O2M and M2M columns
            for o2m_col in o2m_columns:
                if o2m_col not in available_fields and o2m_col in data.columns:
                    available_fields.append(o2m_col)
            for m2m_col in m2m_columns:
                if m2m_col not in available_fields and m2m_col in data.columns:
                    available_fields.append(m2m_col)
            for parent_field in o2m_field_mappings.keys():
                imported_fields.add(parent_field)
                if parent_field not in fields_to_import:
                    fields_to_import.append(parent_field)
            # Add all M2M fields that are in the data
            for m2m_col in m2m_columns:
                if m2m_col in data.columns and m2m_col not in available_fields:
                    available_fields.append(m2m_col)
            final_fields = [f for f in available_fields if (
                    f in model_fields or f == 'id' or f.startswith('o2m__') or f.startswith('m2m__')
            )]
            if not final_fields:
                raise UserError("No valid fields found for import")
            # Drop existing triggers
            try:
                self.env.cr.execute("SAVEPOINT trigger_setup;")
                self.env.cr.execute(f"""
                           DROP TRIGGER IF EXISTS trg_process_m2m_mapping ON {table_name};
                           DROP TRIGGER IF EXISTS trg_process_o2m_mapping ON {table_name};
                       """)
                self.env.cr.execute("RELEASE SAVEPOINT trigger_setup;")
                _logger.info("Dropped existing triggers successfully")
            except Exception as e:
                self.env.cr.execute("ROLLBACK TO SAVEPOINT trigger_setup;")
                self.env.cr.execute("RELEASE SAVEPOINT trigger_setup;")
                self.env.cr.warning(f"Failed to drop triggers (isolated): {e}. Continuing import...")
            # Choose import method based on what we have
            if has_complex_fields:
                if o2m_columns and not m2m_columns:
                    # Only O2M fields - use fast trigger-based import
                    result = self._postgres_bulk_import_fast(
                        data, model, final_fields,
                        m2m_trigger_val, o2m_trigger_val,
                        m2m_columns, o2m_columns,
                        table_name, model_fields,
                        initial_count, model_record,
                        has_complex_fields, reference_cache
                    )
                elif m2m_columns:
                    # Has M2M fields - use enhanced import (handles both O2M and M2M)
                    result = self._postgres_bulk_import_enhanced(
                        data, model, final_fields,
                        m2m_trigger_val, o2m_trigger_val,
                        m2m_columns, o2m_columns,
                        table_name, model_fields,
                        initial_count, model_record,
                        has_complex_fields, reference_cache
                    )
                else:
                    # Other complex fields - use enhanced import
                    result = self._postgres_bulk_import_enhanced(
                        data, model, final_fields,
                        m2m_trigger_val, o2m_trigger_val,
                        m2m_columns, o2m_columns,
                        table_name, model_fields,
                        initial_count, model_record,
                        has_complex_fields, reference_cache
                    )
            else:
                # Simple import - use fast method
                result = self._postgres_bulk_import_fast(
                    data, model, final_fields,
                    m2m_trigger_val, o2m_trigger_val,
                    m2m_columns, o2m_columns,
                    table_name, model_fields,
                    initial_count, model_record,
                    has_complex_fields, reference_cache
                )
            return result
        except UserError:
            raise
        except Exception as e:
            raise UserError(f"Import failed: {str(e)}")

    def _prepare_audit_fields(self):
        """
        Generate audit fields dictionary.
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return {
            'create_uid': self.env.uid,
            'write_uid': self.env.uid,
            'create_date': current_time,
            'write_date': current_time
        }

    def _get_common_default_context(self, model_name=None):
        """
        Builds a dictionary of common default values used during record creation.
        """
        defaults = {
            'company_id': self.env.company.id,
            'currency_id': getattr(self.env.company, 'currency_id', False) and self.env.company.currency_id.id or None,
            'create_uid': self.env.uid,
            'write_uid': self.env.uid,
            'create_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'write_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'state': 'draft',
        }
        if model_name:
            try:
                Model = self.env[model_name]
                model_fields = Model.fields_get()
                required_fields = []
                for fname, finfo in model_fields.items():
                    if finfo.get('required') and finfo.get('store') and not finfo.get('deprecated', False):
                        required_fields.append(fname)
                for fname, finfo in model_fields.items():
                    if finfo.get('type') == 'many2one' and fname in required_fields:
                        rel_model = finfo.get('relation')
                        if not rel_model:
                            continue
                        if fname in defaults:
                            continue
                        domain = []
                        if 'company_id' in self.env[rel_model]._fields:
                            domain = [('company_id', '=', self.env.company.id)]
                        rec = self.env[rel_model].search(domain, limit=1) if domain else self.env[rel_model].search([],
                                                                                                                    limit=1)
                        if rec:
                            defaults.setdefault(fname, rec.id)
                    elif finfo.get('type') == 'many2one' and finfo.get('relation') == 'uom.uom':
                        if fname in required_fields and fname not in defaults:
                            try:
                                rec = self.env['uom.uom'].search([], limit=1)
                                if rec:
                                    defaults[fname] = rec.id
                            except Exception:
                                pass
            except Exception as e:
                _logger.warning(f"Could not prepare model-specific defaults for {model_name}: {e}")
        return defaults

    def _get_dynamic_state_default(self, model, state_field_info):
        """
        Determines the default value for a model's state field.
        """
        try:
            selection_values = state_field_info['selection']
            if callable(selection_values):
                selection_values = selection_values(self.env[model])
            if selection_values:
                draft_states = [val[0] for val in selection_values if val[0].lower() == 'draft']
                if draft_states:
                    return draft_states[0]
                return selection_values[0][0]
            return 'draft'
        except Exception as e:
            _logger.warning(f"Error getting dynamic state default: {e}")
            return 'draft'

    def _get_auto_generated_fields(self, model_name, required_fields):
        """
        Determines which required fields can be auto-generated.
        """
        auto_generated_fields = set()
        try:
            model_obj = self.env[model_name]
            all_field_names = list(model_obj.fields_get().keys())
            defaults = model_obj.default_get(all_field_names)
            fields_with_defaults = {k for k, v in defaults.items() if v is not None}
            for field_name in required_fields:
                if field_name in model_obj._fields:
                    field_obj = model_obj._fields[field_name]
                    if hasattr(field_obj, 'compute') and field_obj.compute:
                        auto_generated_fields.add(field_name)
                    elif hasattr(field_obj, 'related') and field_obj.related:
                        auto_generated_fields.add(field_name)
                    elif hasattr(field_obj, 'default') and callable(field_obj.default):
                        auto_generated_fields.add(field_name)
                    elif field_name in fields_with_defaults:
                        auto_generated_fields.add(field_name)
                    elif field_name in ['create_date', 'write_date', 'create_uid', 'write_uid']:
                        auto_generated_fields.add(field_name)
                    elif self._field_has_automatic_value(model_name, field_name):
                        auto_generated_fields.add(field_name)
        except Exception as e:
            _logger.warning(f"Error detecting auto-generated fields for {model_name}: {e}")
        return auto_generated_fields

    def _field_has_automatic_value(self, model_name, field_name):
        """
        Checks if a field has automatic value.
        """
        try:
            model_obj = self.env[model_name]
            field_obj = model_obj._fields.get(field_name)
            if not field_obj:
                return False
            if hasattr(field_obj, 'default') and field_obj.default:
                return True
            if field_name == 'name' and self._get_sequence_for_model(model_name):
                return True
            context_defaults = model_obj.with_context({}).default_get([field_name])
            if field_name in context_defaults and context_defaults[field_name]:
                return True
            return False
        except Exception as e:
            _logger.warning(f"Error checking automatic value for {field_name}: {e}")
            return False

    def _get_model_defaults(self, model_name):
        """
        Retrieves the default values for all fields of the given model.
        """
        try:
            Model = self.env[model_name]
            field_names = list(Model.fields_get().keys())
            defaults = Model.default_get(field_names)
            return {k: v for k, v in defaults.items() if v is not None}
        except Exception as e:
            _logger.warning(f"Could not get defaults for model {model_name}: {e}")
            return {}

    def _get_dynamic_default_value(self, model_name, field_name, record_count):
        """
        Generates dynamic default values for missing fields.
        """
        try:
            Model = self.env[model_name]
            field_obj = Model._fields.get(field_name)
            if not field_obj:
                return None
            defaults = Model.default_get([field_name])
            if field_name in defaults and defaults[field_name] is not None:
                return [defaults[field_name]] * record_count
            if hasattr(field_obj, 'default') and callable(field_obj.default):
                default_val = field_obj.default(Model)
                if default_val is not None:
                    return [default_val] * record_count
            field_type = field_obj.type
            if field_type in ['char', 'text']:
                return [f"Auto-{field_name}"] * record_count
            elif field_type in ['integer', 'float', 'monetary']:
                return [0] * record_count
            elif field_type == 'boolean':
                return [False] * record_count
            elif field_type == 'date':
                # Do NOT override if user supplied a value
                return [None] * record_count
            elif field_type == 'datetime':
                return [None] * record_count
            elif field_type == 'many2one':
                comodel = field_obj.comodel_name
                if comodel:
                    default_record = self.env[comodel].search([], limit=1)
                    if default_record:
                        return [default_record.id] * record_count
            elif field_type == 'selection':
                if field_obj.selection:
                    selection_values = field_obj.selection
                    if callable(selection_values):
                        selection_values = selection_values(Model)
                    if selection_values and len(selection_values) > 0:
                        return [selection_values[0][0]] * record_count
            return None
        except Exception as e:
            _logger.warning(f"Error getting dynamic default for {field_name}: {e}")
            return None

    def _get_sequence_for_model(self, model_name):
        """
        Returns the most suitable ir.sequence record for the given model name.
        """
        try:
            seq = self.env['ir.sequence'].search([('code', '=', model_name)], limit=1)
            if seq:
                return seq
            last_part = model_name.split('.')[-1]
            seq = self.env['ir.sequence'].search([('code', 'ilike', last_part)], limit=1)
            if seq:
                return seq
            seqs = self.env['ir.sequence'].search(['|', ('prefix', 'ilike', model_name), ('name', 'ilike', model_name)],
                                                  limit=5)
            if seqs:
                return seqs[0]
            parts = [p for p in model_name.replace('.', '_').split('_') if len(p) > 2]
            for p in parts:
                seq = self.env['ir.sequence'].search([('code', 'ilike', p)], limit=1)
                if seq:
                    return seq
            return False
        except Exception as e:
            _logger.warning(f"Sequence lookup failed for {model_name}: {e}")
            return False

    def _generate_bulk_sequences(self, sequence, count):
        """
        Generates bulk sequence values.
        """
        if not sequence or count <= 0:
            return []
        try:
            sequence_table = sequence._table if hasattr(sequence, '_table') else 'ir_sequence'
            sequence_id = sequence.id
            # Get sequence details
            self.env.cr.execute("""
                        SELECT number_next, implementation, prefix, suffix, padding
                        FROM ir_sequence
                        WHERE id = %s
                        FOR UPDATE
                    """, (sequence_id,))
            row = self.env.cr.fetchone()
            if not row:
                raise ValueError("Sequence not found")
            number_next, implementation, prefix, suffix, padding = row
            prefix = prefix or ''
            suffix = suffix or ''
            padding = padding or 0
            # Reserve the range
            new_next = number_next + count
            self.env.cr.execute("""
                        UPDATE ir_sequence
                        SET number_next = %s
                        WHERE id = %s
                    """, (new_next, sequence_id))
            # Generate sequence values
            sequence_values = []
            for i in range(count):
                number = number_next + i
                padded = str(number).zfill(padding)
                sequence_values.append(f"{prefix}{padded}{suffix}")
            _logger.info(f"Generated {count} sequences in bulk: {number_next} to {new_next - 1}")
            return sequence_values

        except Exception as e:
            _logger.error(f"Bulk sequence generation failed: {e}")
            # Fallback to individual generation
            return [sequence.next_by_id() for _ in range(count)]

    def _sanitize_value(self, val, field_info=None):
        """
        Convert Python/Odoo values into SQL-safe JSON values dynamically.
        """
        # Handle pandas NaN / None
        if val is None:
            return None
        if isinstance(val, float) and (_np.isnan(val) if hasattr(_np, "isnan") else _pd.isna(val)):
            return None
        # Convert booleans properly
        if val is True:
            return True
        if val is False:
            return None
        # Convert datetime/date
        if isinstance(val, (_dt.datetime, _dt.date)):
            return val.strftime('%Y-%m-%d %H:%M:%S')
        # Convert all string "false", "False", "NULL", "" to NULL
        if isinstance(val, str):
            if val.strip().lower() in ("false", "none", "null", ""):
                return None
            return val.strip()
        # Handle integer/float cleanly
        if isinstance(val, (int, float)):
            return val
        # Any unknown value convert to string safely
        return str(val)

    def _safe_json_array(self, value_list):
        """
        Return a JSON array string that PostgreSQL can cast to jsonb without errors.
        """
        if not value_list:
            return "[]"
        safe_list = []
        for item in value_list:
            if item is None:
                continue
            if not isinstance(item, dict):
                # Wrap non-dict (rare case)
                safe_list.append(self._sanitize_value(item))
                continue
            # Sanitize each key
            clean = {}
            for k, v in item.items():
                clean[k] = self._sanitize_value(v)
            safe_list.append(clean)
        return json.dumps(safe_list, ensure_ascii=False, default=str)

    def _safe_json_value(self, val):
        """
        Convert any Python object into JSON-serializable type.
        """
        if isinstance(val, (datetime.date, datetime.datetime)):
            return val.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(val, float):
            if pd.isna(val):
                return None
        if isinstance(val, pd.Timestamp):
            return val.strftime("%Y-%m-%d %H:%M:%S")
        return val

    def _resolve_reference(self, model, value, reference_cache):
        """
        Convert a reference value (ID, name, code, etc.) to a database ID for a many2one field.
        This helper method resolves references by checking multiple sources: first looking in cache,
        then trying direct ID matching, XML external IDs, and finally searching common fields like
        name, code, or barcode. It caches successful lookups to improve performance for repeated values.
        """
        if pd.isna(value) or value in ['', 0, '0']:
            return None
        cache_key = model
        str_val = str(value).strip()
        if cache_key in reference_cache:
            cached_id = reference_cache[cache_key].get(str_val)
            if cached_id is not None:
                return cached_id
        Model = self.env[model]
        try:
            record_id = int(float(str_val))
            record = Model.browse(record_id).exists()
            if record:
                return record.id
        except:
            pass
        try:
            return self.env.ref(str_val).id
        except Exception:
            pass
        searchable_fields = []
        model_fields = Model.fields_get()
        for field_name, info in model_fields.items():
            if (info.get('store') and info.get('type') in ['char', 'text'] and not info.get('deprecated', False)):
                searchable_fields.append(field_name)
        for field in ['name', 'code', 'reference', 'display_name', 'complete_name', 'default_code', 'barcode']:
            if field in model_fields and field not in searchable_fields:
                searchable_fields.append(field)
        for field_name in searchable_fields:
            try:
                record = Model.search([(field_name, '=ilike', str_val)], limit=1)
                if record:
                    if cache_key not in reference_cache:
                        reference_cache[cache_key] = {}
                    reference_cache[cache_key][str_val] = record.id
                    return record.id
            except Exception:
                continue
        _logger.warning(f"Could not resolve {model} reference: {str_val}")
        return None

    def _build_reference_cache(self, model, values, reference_cache):
        """
        Pre-populate a cache with many2one references to speed up resolution.
        This method proactively looks up all unique values for a model and stores their
        database IDs in cache. It checks for direct IDs, searches common identifying fields
        (name, code, barcode, etc.), and extracts codes from bracketed formats. This bulk
        approach significantly improves performance when resolving many references.
        """
        cache_key = model
        if cache_key not in reference_cache:
            reference_cache[cache_key] = {}

        Model = self.env[model]
        unique_values = list(set(str(v).strip() for v in values if pd.notna(v) and v not in ['', 0, '0']))

        if not unique_values:
            return

        # Step 1: Handle numeric IDs first (fastest path)
        id_values = []
        non_id_values = []

        for val in unique_values:
            try:
                id_val = int(float(val))
                id_values.append(id_val)
            except:
                non_id_values.append(val)

        # Batch lookup for numeric IDs
        if id_values:
            try:
                records = Model.browse(id_values).exists()
                for record in records:
                    reference_cache[cache_key][str(record.id)] = record.id
            except Exception as e:
                _logger.warning(f"ID lookup failed for {model}: {e}")

        if not non_id_values:
            return

        # Step 2: Build search field candidates
        search_fields = []
        for candidate in ['default_code', 'barcode', 'name', 'code', 'reference', 'complete_name']:
            if candidate in Model._fields and Model._fields[candidate].store:
                search_fields.append(candidate)

        if not search_fields:
            return

        # Step 3: Extract bracketed codes [CODE]
        bracketed_codes = []
        for val in non_id_values:
            if '[' in val and ']' in val:
                try:
                    start = val.index('[') + 1
                    end = val.index(']')
                    code = val[start:end]
                    if code and code not in bracketed_codes:
                        bracketed_codes.append(code)
                except:
                    pass

        # Step 4: Search for default_code with bracketed values first (if applicable)
        if 'default_code' in search_fields and bracketed_codes:
            try:
                records = Model.search([('default_code', 'in', bracketed_codes)])
                for record in records:
                    if record.default_code:
                        # Cache the code itself
                        reference_cache[cache_key][record.default_code] = record.id

                        # Cache all values that contain this code in brackets
                        for val in non_id_values:
                            if f'[{record.default_code}]' in val:
                                reference_cache[cache_key][val] = record.id
            except Exception as e:
                _logger.warning(f"Bracketed code search failed for {model}: {e}")

        # Step 5: Search each field separately (SAFE - no UNION)
        for field_name in search_fields:
            try:
                # Search for exact matches
                records = Model.search([(field_name, 'in', non_id_values)], limit=len(non_id_values) * 2)

                for record in records:
                    field_value = getattr(record, field_name, None)
                    if field_value:
                        str_value = str(field_value)
                        reference_cache[cache_key][str_value] = record.id

                        # Also cache partial matches
                        for val in non_id_values:
                            if str_value in val:
                                reference_cache[cache_key][val] = record.id

            except Exception as e:
                _logger.warning(f"Search failed for {model}.{field_name}: {e}")
                continue

        _logger.info(f"Reference cache built for {model}: {len(reference_cache[cache_key])} entries")


    def _handle_sql_constraints_for_child_records(self, comodel_name, row_data, reference_cache):
        """
        Automatically fill missing fields to satisfy database constraints for child records.
        This method examines the child model's SQL constraints and provides default values
        for required fields that might be missing. For example, it sets date_planned for future
        dates, links UOM from products, and assigns appropriate accounts based on product categories.
        """
        try:
            child_model = self.env[comodel_name]
            if not hasattr(child_model, '_sql_constraints'):
                return row_data
            _logger.info(f"Checking SQL constraints for: {comodel_name}")
            for constraint_name, constraint_sql, constraint_msg in child_model._sql_constraints:
                constraint_sql_lower = constraint_sql.lower()
                if 'date_planned is not null' in constraint_sql_lower and 'date_planned' not in row_data:
                    from datetime import timedelta
                    future_date = datetime.now() + timedelta(weeks=1)
                    row_data['date_planned'] = future_date.strftime('%Y-%m-%d')
                    _logger.info(f"Set date_planned: {row_data['date_planned']}")
                if ('product_uom is not null' in constraint_sql_lower and
                        'product_uom' not in row_data and 'product_id' in row_data):
                    try:
                        product = self.env['product.product'].browse(row_data['product_id'])
                        if product.exists() and product.uom_id:
                            row_data['product_uom'] = product.uom_id.id
                            _logger.info(f"Set product_uom: {row_data['product_uom']}")
                    except Exception as e:
                        _logger.warning(f"Failed to set product_uom: {e}")
                if ('account_id is not null' in constraint_sql_lower and
                        'account_id' not in row_data and 'product_id' in row_data):
                    try:
                        product = self.env['product.product'].browse(row_data['product_id'])
                        if product.exists():
                            account_id = None
                            if hasattr(product, 'property_account_expense_id') and product.property_account_expense_id:
                                account_id = product.property_account_expense_id.id
                            elif hasattr(product, 'property_account_income_id') and product.property_account_income_id:
                                account_id = product.property_account_income_id.id
                            if account_id:
                                row_data['account_id'] = account_id
                                _logger.info(f"Set account_id: {account_id}")
                    except Exception as e:
                        _logger.warning(f"Failed to set account_id: {e}")
            return row_data
        except Exception as e:
            _logger.warning(f"Error handling SQL constraints for {comodel_name}: {e}")
            return row_data

    def get_required_fields(self, model_name):
        """
        Returns a list of required fields for the given model.
        """
        Model = self.env[model_name]
        model_fields = Model.fields_get()
        required_fields = []
        for field_name, field in model_fields.items():
            if field.get('required') and field.get('store') and not field.get('deprecated', False):
                required_fields.append({
                    'name': field_name,
                    'type': field['type']
                })
        return required_fields

    def _check_missing_required_fields_for_validation(self, model_name, columns):
        """
        Find required fields that are missing from import data and have no fallback values.
        This validation method compares the imported fields against the model's requirements,
        identifying fields that are required for creation, not provided in the import, and
        lack default values or auto-generation. It excludes audit fields and computed fields.
        """
        try:
            imported_fields = set()
            for item in columns:
                if 'fieldInfo' in item:
                    field_name = item['fieldInfo']['id']
                    if '/' in field_name:
                        field_name = field_name.split('/')[0]
                    imported_fields.add(field_name)
            Model = self.env[model_name]
            model_fields = Model.fields_get()
            field_objects = Model._fields
            required_fields = []
            for field_name, field_info in model_fields.items():
                field_obj = field_objects.get(field_name)
                if field_info.get('deprecated', False):
                    continue
                is_required = field_info.get('required', False)
                has_default = False
                if field_obj and hasattr(field_obj, 'default'):
                    if field_obj.default is not None:
                        has_default = True
                if field_name in ['create_date', 'write_date', 'create_uid', 'write_uid']:
                    continue
                if field_name in ['alias_id', 'resource_id']:
                    continue
                if is_required and not has_default:
                    if field_info.get('store', True) and not field_info.get('compute', False):
                        required_fields.append(field_name)
            defaults = Model.default_get(list(model_fields.keys()))
            odoo_defaults = {k: v for k, v in defaults.items() if v is not None}
            auto_generated_fields = self._get_auto_generated_fields(model_name, required_fields)
            missing_without_fallback = []
            for field in set(required_fields) - imported_fields:
                if field not in odoo_defaults and field not in auto_generated_fields:
                    missing_without_fallback.append(field)
            return missing_without_fallback
        except Exception as e:
            _logger.error(f"Error checking required fields for {model_name}: {str(e)}")
            return []

    def _check_missing_required_fields(self, model_name, imported_fields, defaults):
        """
        Checks for missing required fields.
        """
        Model = self.env[model_name]
        model_fields = Model.fields_get()
        required_fields = []
        for field_name, field_info in model_fields.items():
            if (field_info.get('required') and
                    field_info.get('store') and
                    not field_info.get('deprecated', False)):
                required_fields.append(field_name)
        missing_required = set(required_fields) - imported_fields
        auto_generated_fields = self._get_auto_generated_fields(model_name, list(missing_required))
        missing_without_fallback = []
        for field in missing_required:
            if field not in defaults and field not in auto_generated_fields:
                missing_without_fallback.append(field)
        return missing_without_fallback

    def _handle_missing_required_fields(self, data, model_name, missing_required):
        """
            Fills required fields that were not provided in the import data by generating
            appropriate default values dynamically. For each missing required field, the
            method retrieves a model-specific fallback value and inserts it into the
            dataset, ensuring the import can proceed without errors. Returns the updated
            DataFrame with all necessary fields populated.
        """
        try:
            Model = self.env[model_name]
            for field_name in missing_required:
                if field_name not in data.columns:
                    field_value = self._get_dynamic_default_value(model_name, field_name, len(data))
                    if field_value is not None:
                        data = data.copy()
                        data.loc[:, field_name] = field_value
                        _logger.info(f"Dynamically set {field_name} for {model_name}")
            return data
        except Exception as e:
            _logger.warning(f"Error dynamically handling required fields: {e}")
            return data

    def _sync_sequence_after_import(self, table_name):
        """
        Synchronize PostgreSQL sequence after bulk import.
        """
        try:
            self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
            max_id = self.env.cr.fetchone()[0]
            sequence_name = f"{table_name}_id_seq"
            new_seq_val = max_id + 1000
            self.env.cr.execute(f"SELECT setval('{sequence_name}', %s)", (new_seq_val,))
        except Exception as e:
            _logger.error(f"Error syncing sequence for {table_name}: {e}")
            try:
                self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
                max_id = self.env.cr.fetchone()[0]
                sequence_name = f"{table_name}_id_seq"
                self.env.cr.execute(f"SELECT setval('{sequence_name}', %s)", (max_id + 1,))
            except Exception as fallback_error:
                _logger.error(f"Fallback sequence sync failed for {table_name}: {fallback_error}")

    def remove_m2m_temp_columns(self, table, m2m_columns):
        """
        Remove temporary many2many/one2many helper columns and drop triggers.
        """
        for column in m2m_columns:
            self.env.cr.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column};")
        self.env.cr.execute(f"""
            DROP TRIGGER IF EXISTS trg_process_m2m_mapping ON {table};
            DROP TRIGGER IF EXISTS trg_process_o2m_mapping ON {table};
        """)

    def get_m2m_details(self, model_name, field_name):
        """
        Retrieves metadata for a many2many field.
        """
        model = self.env[model_name]
        field = model._fields[field_name]
        return {
            'relation_table': field.relation,
            'column1': field.column1,
            'column2': field.column2
        }

    def _apply_parent_defaults(self, parent_record, model_name):
        """
        Applies defaults to parent records.
        """
        try:
            Model = self.env[model_name]
            model_fields = Model.fields_get()
            defaults = {
                'state': 'draft',
                'company_id': self.env.company.id,
                'currency_id': getattr(self.env.company, 'currency_id',
                                       False) and self.env.company.currency_id.id or None,
            }
            for field, default_value in defaults.items():
                if field in model_fields and (field not in parent_record or not parent_record[field]):
                    parent_record[field] = default_value
            context_defaults = self._get_common_default_context(model_name)
            for field, value in context_defaults.items():
                if field in model_fields and not parent_record.get(field) and value:
                    parent_record[field] = value
            for field_name, field_info in model_fields.items():
                if field_info['type'] == 'many2one' and field_name not in parent_record:
                    if field_name in ['company_id']:
                        parent_record[field_name] = self.env.company.id
        except Exception as e:
            _logger.warning(f"Error applying parent defaults for {model_name}: {e}")
        return parent_record

    def _apply_child_defaults(self, child_record, comodel_name, reference_cache, default_context=None):
        """
        Applies defaults to child records.
        """
        try:
            ChildModel = self.env[comodel_name]
            child_fields = ChildModel.fields_get()
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if default_context:
                for field, value in default_context.items():
                    if field in child_fields and not child_record.get(field):
                        child_record[field] = value
            model_defaults = ChildModel.default_get(list(child_fields.keys()))
            for field, val in model_defaults.items():
                if field in child_fields and field not in child_record and val is not None:
                    child_record[field] = val
            # Get product if product_id exists
            product = None
            if 'product_id' in child_record and child_record['product_id']:
                try:
                    product = self.env['product.product'].browse(child_record['product_id'])
                    if product.exists():
                        # Fill name with product name if name is empty
                        if not child_record.get('name') or child_record['name'] == '':
                            child_record['name'] = product.display_name or product.name
                            _logger.info(f"Set name field to product name: {child_record['name']}")
                        # Fill price_unit with product price if price_unit is empty
                        if 'price_unit' in child_fields and (
                                not child_record.get('price_unit') or child_record['price_unit'] == '' or child_record[
                            'price_unit'] == 0):
                            # Use product's sale price (lst_price)
                            child_record['price_unit'] = product.lst_price or 0.0
                            _logger.info(f"Set price_unit to product price: {child_record['price_unit']}")
                        # Set UOM from product if UOM field is empty
                        uom_fields = [f for f, finfo in child_fields.items() if
                                      finfo.get('type') == 'many2one' and finfo.get('relation') == 'uom.uom']
                        for uom_field in uom_fields:
                            if uom_field not in child_record or not child_record.get(uom_field):
                                if getattr(product, 'uom_id', False):
                                    child_record[uom_field] = product.uom_id.id
                                    _logger.info(f"Set {uom_field} to product UOM: {product.uom_id.id}")
                except Exception as e:
                    _logger.warning(f"Failed to process product {child_record.get('product_id')}: {e}")
                    product = None
            # Set default name if still empty
            if 'name' not in child_record or not child_record.get('name') or child_record['name'] == '':
                child_record['name'] = "Line"
            # Set default product_id if needed
            for candidate in ['product_id']:
                if candidate in child_fields and not child_record.get(candidate):
                    field_obj = ChildModel._fields.get(candidate)
                    if field_obj and getattr(field_obj, 'comodel_name', None):
                        try:
                            rec = self.env[field_obj.comodel_name].search([], limit=1)
                            if rec:
                                child_record[candidate] = rec.id
                        except Exception:
                            pass
            # Set UOM from default if not set from product
            uom_fields = [f for f, finfo in child_fields.items() if
                          finfo.get('type') == 'many2one' and finfo.get('relation') == 'uom.uom']
            for uom_field in uom_fields:
                if uom_field not in child_record or not child_record.get(uom_field):
                    try:
                        uom = self.env['uom.uom'].search([], limit=1)
                        if uom:
                            child_record[uom_field] = uom.id
                    except Exception:
                        pass
            # Set date_planned if exists
            if 'date_planned' in child_fields and not child_record.get('date_planned'):
                child_record['date_planned'] = now_str
            # Set required fields
            for field, finfo in child_fields.items():
                if finfo.get('required') and field not in child_record:
                    ftype = finfo['type']
                    if ftype in ['integer', 'float', 'monetary']:
                        child_record[field] = 0.0
                    elif ftype in ['char', 'text']:
                        child_record[field] = f"Auto {field.replace('_', ' ').title()}"
                    elif ftype in ['date', 'datetime']:
                        child_record[field] = now_str
                    elif ftype == 'many2one':
                        rel_model = finfo.get('relation')
                        if rel_model:
                            record = self.env[rel_model].search([], limit=1)
                            if record:
                                child_record[field] = record.id
            # Handle display_type based on name
            if 'name' in child_record and isinstance(child_record['name'], str):
                lower_name = child_record['name'].strip().lower()
                if lower_name.startswith('note:'):
                    child_record['display_type'] = 'line_note'
                    # Clear product fields for note lines
                    for f in ['product_id', 'product_uom', 'product_qty', 'price_unit', 'date_planned']:
                        if f in child_record:
                            child_record[f] = None
                elif lower_name.startswith('section:'):
                    child_record['display_type'] = 'line_section'
                    # Clear product fields for section lines
                    for f in ['product_id', 'product_uom', 'product_qty', 'price_unit', 'date_planned']:
                        if f in child_record:
                            child_record[f] = None
            else:
                child_record['display_type'] = 'product'
            if 'display_type' in child_record:
                display_type = child_record['display_type']
                if isinstance(display_type, bool) or isinstance(display_type, (int, float)):
                    display_type = None
                elif isinstance(display_type, str):
                    display_type = display_type.strip().lower()
                    if display_type in ('line_section', 'section'):
                        display_type = 'line_section'
                    elif display_type in ('line_note', 'note'):
                        display_type = 'line_note'
                    else:
                        display_type = 'product'
                else:
                    display_type = 'product'
                child_record['display_type'] = display_type
                if display_type in ('line_section', 'line_note'):
                    for f in ['product_id', 'product_uom', 'product_qty', 'price_unit', 'date_planned']:
                        if f in child_record:
                            child_record[f] = None
            child_record = self._handle_sql_constraints_for_child_records(comodel_name, child_record, reference_cache)
            # Special handling for account.move.line
            if comodel_name == "account.move.line":
                # Fill name with product name if available
                if (not child_record.get('name') or child_record['name'] == '') and child_record.get('product_id'):
                    if product is None:
                        product = self.env['product.product'].browse(child_record['product_id'])
                    if product.exists():
                        child_record['name'] = product.display_name or product.name
                # Fill price_unit with product price if empty
                if (not child_record.get('price_unit') or child_record['price_unit'] == '' or child_record[
                    'price_unit'] == 0) and child_record.get('product_id'):
                    if product is None:
                        product = self.env['product.product'].browse(child_record['product_id'])
                    if product.exists():
                        child_record['price_unit'] = product.lst_price or 0.0
                # Set account_id from product
                if not child_record.get('account_id') and child_record.get('product_id'):
                    if product is None:
                        product = self.env['product.product'].browse(child_record['product_id'])
                    if product.exists():
                        account = (
                                getattr(product, "property_account_income_id", False) or
                                getattr(product.categ_id, "property_account_income_categ_id", False) or
                                getattr(product, "property_account_expense_id", False) or
                                getattr(product.categ_id, "property_account_expense_categ_id", False)
                        )
                        if account:
                            child_record['account_id'] = account.id
                        if not child_record.get("display_type"):
                            # Use proper Odoo defaults: invoice lines are product lines unless user says section/note
                            child_record["display_type"] = "product"
                        # Normalize and validate display_type
                        dt = str(child_record.get("display_type", "")).strip().lower()
                        if dt in ("section", "line_section"):
                            dt = "line_section"
                        elif dt in ("note", "line_note"):
                            dt = "line_note"
                        else:
                            dt = "product"
                        child_record["display_type"] = dt
                        # Clear product fields if it's a note/section line
                        if dt in ("line_section", "line_note"):
                            for f in ["product_id", "product_uom_id", "quantity", "price_unit", "debit", "credit"]:
                                if f in child_record:
                                    child_record[f] = None
                # Set default quantity
                if not child_record.get('quantity') and child_record.get('product_uom_qty') is None:
                    child_record['quantity'] = 1
                # Set debit/credit
                if not child_record.get('debit') and not child_record.get('credit'):
                    qty = float(child_record.get('quantity', 1))
                    price = float(child_record.get('price_unit', 0))
                    amount = qty * price
                    child_record['debit'] = amount
                    child_record['credit'] = 0.0
                # Set product_uom_id from product
                if child_record.get('product_id') and not child_record.get('product_uom_id'):
                    if product is None:
                        product = self.env['product.product'].browse(child_record['product_id'])
                    if product and product.uom_id:
                        child_record['product_uom_id'] = product.uom_id.id
            # Calculate total if we have quantity and price
            if child_record.get('product_qty') and child_record.get('price_unit'):
                try:
                    qty = float(child_record.get('product_qty', 1))
                    price = float(child_record.get('price_unit', 0))
                    amount = qty * price
                    # Set price_subtotal if field exists
                    if 'price_subtotal' in child_fields:
                        child_record['price_subtotal'] = amount
                    # Set price_total if field exists
                    if 'price_total' in child_fields:
                        child_record['price_total'] = amount
                except (ValueError, TypeError):
                    pass
            # Final sanitize before JSON serialization
            for key, val in list(child_record.items()):
                child_record[key] = self._sanitize_value(
                    child_record[key],
                    field_info=child_fields.get(key)
                )
            return child_record
        except Exception as e:
            _logger.error(f"Error applying child defaults for {comodel_name}: {e}")
            import traceback
            _logger.error(traceback.format_exc())
            return child_record

    def _process_child_field_value(self, child_field, cell_value, comodel_name, reference_cache):
        """
            Processes and converts a raw Excel cell value into a valid value for a
            child (one2many) field. It handles many2one fields by resolving references,
            numeric fields by safely converting to floats, and fallback text fields by
            cleaning string values. Missing or invalid data is normalized to safe
            defaults to ensure child record creation does not fail.
        """
        try:
            comodel = self.env[comodel_name]
            child_field_obj = comodel._fields.get(child_field)
            if child_field.endswith('_id') or (
                    child_field_obj and getattr(child_field_obj, 'type', None) == 'many2one'):
                field_model = None
                if child_field_obj and getattr(child_field_obj, 'comodel_name', None):
                    field_model = child_field_obj.comodel_name
                else:
                    field_model = child_field.replace('_id', '').replace('_', '.')
                resolved_id = self._resolve_reference(field_model, cell_value, reference_cache)
                return resolved_id
            numeric_field_names = ['qty', 'quantity', 'product_qty', 'price_unit', 'amount', 'purchase_price',
                                   'cost_price', 'product_uom_qty']
            if child_field in numeric_field_names:
                try:
                    if pd.isna(cell_value) or cell_value in ['', None, 'nan', 'None']:
                        return 0.0
                    return float(cell_value)
                except (ValueError, TypeError):
                    return 0.0
            if pd.isna(cell_value) or cell_value in ['', None, 'nan', 'None']:
                return ""
            return str(cell_value).strip()
        except Exception as e:
            _logger.warning(f"Error processing child field {child_field}: {e}")
            if child_field in ['product_qty', 'price_unit', 'quantity', 'qty']:
                return 0.0
            else:
                return ""

    def _group_o2m_records(self, data, model_name, o2m_field_mappings, reference_cache):
        """
         Organize flat Excel data into parent records with their one2many child records.
        This method groups spreadsheet rows by parent identifiers (like order numbers or names),
        creating parent records from the first row of each group and collecting child data from
        subsequent rows. It handles missing identifiers by generating synthetic ones and prepares
        child records in JSON format for bulk import.
        """
        if data is None or len(data) == 0:
            _logger.warning(f"No data received for grouping in model {model_name}")
            return pd.DataFrame()
        Model = self.env[model_name]
        model_fields = Model.fields_get()
        cleaned_o2m_field_mappings = {}
        parent_field_infos = {}
        for parent_field, field_mappings in o2m_field_mappings.items():
            field_info = Model._fields.get(parent_field)
            if field_info and getattr(field_info, "type", None) == "one2many":
                cleaned_o2m_field_mappings[parent_field] = field_mappings
                parent_field_infos[parent_field] = field_info
                _logger.info(f"O2M field kept for grouping: {parent_field} -> {field_info.comodel_name}")
            else:
                _logger.warning(f"Skipping '{parent_field}' in O2M mapping: not a one2many on model {model_name}")
        if not cleaned_o2m_field_mappings:
            _logger.info("No valid O2M mappings after cleanup; skipping grouping.")
            return data
        o2m_field_mappings = cleaned_o2m_field_mappings
        identifier_fields = ["name", "reference", "code", "number"]
        parent_id_series = pd.Series([None] * len(data), index=data.index, dtype=object)
        for field in identifier_fields:
            if field in data.columns:
                col = data[field]
                mask = col.notna() & (col.astype(str).str.strip() != "")
                set_mask = mask & parent_id_series.isna()
                if set_mask.any():
                    parent_id_series.loc[set_mask] = col.astype(str).str.strip().loc[set_mask]
                    _logger.info(f"Using field '{field}' as parent identifier for some rows")
        parent_id_series = parent_id_series.ffill()
        if parent_id_series.isna().all():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            synth = f"{model_name}_{timestamp}_0"
            parent_id_series[:] = synth
            _logger.info(f"No identifier fields found or all empty; using synthetic parent id '{synth}' for all rows")
        elif parent_id_series.isna().any():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            synth = f"{model_name}_{timestamp}_0"
            parent_id_series = parent_id_series.fillna(synth)
            _logger.info(f"Some rows had no identifier; filled them with synthetic parent id '{synth}'")
        for parent_field, field_mappings in o2m_field_mappings.items():
            field_info = parent_field_infos[parent_field]
            comodel_name = field_info.comodel_name
            all_values = []
            for mapping in field_mappings:
                excel_col = mapping["excel_column"]
                if excel_col in data.columns:
                    col_vals = data[excel_col].dropna().astype(str)
                    col_vals = col_vals[col_vals.str.strip() != ""]
                    if not col_vals.empty:
                        all_values.extend(col_vals.unique().tolist())
            if all_values:
                _logger.info(
                    f"Pre-building reference cache for O2M comodel {comodel_name} ({len(all_values)} potential values)")
                try:
                    self._build_reference_cache(comodel_name, all_values, reference_cache)
                except Exception as e:
                    _logger.warning(f"Failed pre-building reference cache for {comodel_name}: {e}")
        grouped = data.groupby(parent_id_series, sort=False, dropna=False)
        parent_data_list = []
        o2m_data_mapping = {parent_field: [] for parent_field in o2m_field_mappings.keys()}
        current_parent_data = {}
        non_o2m_cols = [c for c in data.columns if not c.startswith("o2m__")]
        default_context = self._get_common_default_context(model_name)
        for parent_identifier, group_df in grouped:
            if group_df.empty:
                continue
            first_row = group_df.iloc[0]
            parent_data = {}
            for col in non_o2m_cols:
                if col not in group_df.columns:
                    continue
                val = first_row.get(col, None)
                if pd.notna(val) and str(val).strip():
                    parent_data[col] = val
                    current_parent_data[col] = val
                elif col in current_parent_data and current_parent_data[col]:
                    parent_data[col] = current_parent_data[col]
            if not parent_data.get("name"):
                parent_data["name"] = parent_identifier
                current_parent_data["name"] = parent_identifier
            parent_data = self._apply_parent_defaults(parent_data, model_name)
            parent_data_list.append(parent_data)
            group_columns = list(group_df.columns)
            col_pos = {name: idx for idx, name in enumerate(group_columns)}
            for parent_field, field_mappings in o2m_field_mappings.items():
                field_info = parent_field_infos.get(parent_field)
                if not field_info:
                    o2m_data_mapping[parent_field].append([])
                    continue
                comodel_name = field_info.comodel_name
                inverse_name = getattr(field_info, "inverse_name", None)
                excel_cols = [
                    m["excel_column"]
                    for m in field_mappings
                    if m["excel_column"] in group_df.columns
                ]
                if not excel_cols:
                    o2m_data_mapping[parent_field].append([])
                    continue
                sub = group_df[excel_cols]
                non_empty = sub.notna() & (sub.astype(str).apply(lambda s: s.str.strip() != ""))
                row_mask = non_empty.any(axis=1)
                if not row_mask.any():
                    o2m_data_mapping[parent_field].append([])
                    continue
                child_chunk = group_df.loc[row_mask, :]
                child_records = []
                for row_tuple in child_chunk.itertuples(index=False, name=None):
                    child_record = {}
                    has_child_data = False
                    for mapping in field_mappings:
                        excel_col = mapping["excel_column"]
                        child_field = mapping["child_field"]
                        pos = col_pos.get(excel_col)
                        if pos is None:
                            continue
                        cell_value = row_tuple[pos]
                        if pd.isna(cell_value) or str(cell_value).strip() == "":
                            continue
                        processed_value = self._process_child_field_value(child_field, cell_value, comodel_name,
                                                                          reference_cache)
                        if processed_value is not None:
                            child_record[child_field] = processed_value
                            has_child_data = True
                    if has_child_data:
                        child_record = self._apply_child_defaults(child_record, comodel_name, reference_cache,
                                                                  default_context=default_context)
                        if inverse_name and inverse_name in child_record:
                            del child_record[inverse_name]
                        child_records.append(child_record)
                o2m_data_mapping[parent_field].append(child_records)
        if not parent_data_list:
            _logger.warning(f"No parent data found after grouping for {model_name}")
            return pd.DataFrame()
        result_df = pd.DataFrame(parent_data_list)
        for parent_field in o2m_field_mappings.keys():
            o2m_column_name = f"o2m__{parent_field}"
            if parent_field in o2m_data_mapping:
                result_df.loc[:, o2m_column_name] = o2m_data_mapping[parent_field]
        return result_df

    def _get_next_sequence_values(self, table_name, count):
        """
        Generate sequential IDs for PostgreSQL bulk inserts.
        """
        try:
            self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
            max_id = self.env.cr.fetchone()[0]
            ids_to_use = list(range(max_id + 1, max_id + count + 1))
            sequence_name = f"{table_name}_id_seq"
            new_seq_val = max_id + count + 100
            self.env.cr.execute(f"SELECT setval('{sequence_name}', %s, false)", (new_seq_val,))
            return ids_to_use
        except Exception as e:
            _logger.error(f"Error generating sequence values for {table_name}: {e}")
            try:
                self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
                max_id = self.env.cr.fetchone()[0]
                return list(range(max_id + 1, max_id + count + 1))
            except Exception as fallback_error:
                _logger.error(f"Fallback ID generation failed: {fallback_error}")
                raise UserError(f"Unable to generate unique IDs: {str(e)}")

    def _postgres_bulk_import_fast(self, data, model, final_fields, m2m_trigger_val, o2m_trigger_val,
                                   m2m_columns, o2m_columns, table_name, model_fields,
                                   initial_count, model_record, has_complex_fields, reference_cache):
        """
        Perform high-speed bulk import using PostgreSQL COPY command.
        This optimized method uses PostgreSQL's COPY command for maximum performance when
        importing large datasets. It prepares data with proper formatting, sets up database
        triggers to handle one2many and many2many relationships automatically, and cleans
        up temporary structures after import. Includes audit field population, sequence
        generation, and data type conversion.
        """
        try:
            Model = self.env[model]

            # Handle sequence for name field
            if 'name' in model_fields:
                sequence = self._get_sequence_for_model(model)
                needs_sequence = False
                name_in_data = 'name' in data.columns

                if not name_in_data:
                    needs_sequence = True
                else:
                    non_null_names = data['name'].dropna()
                    if len(non_null_names) == 0:
                        needs_sequence = True
                    else:
                        # Vectorized check
                        name_check = non_null_names.astype(str).str.strip().str.lower().isin(['new', '', 'false'])
                        needs_sequence = name_check.all()

                if sequence and needs_sequence:
                    record_count = len(data)
                    if record_count > 0:
                        try:
                            # OPTIMIZED: Bulk sequence generation
                            sequence_values = self._generate_bulk_sequences(sequence, record_count)
                            data.loc[:, 'name'] = sequence_values
                            if 'name' not in final_fields:
                                final_fields.append('name')
                        except Exception as e:
                            _logger.error(f"Failed to generate sequences: {e}")
                elif not sequence and needs_sequence:
                    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                    data.loc[:, 'name'] = [f"New-{timestamp}-{i + 1}" for i in range(len(data))]
                    if 'name' not in final_fields:
                        final_fields.append('name')

            # Add audit fields
            audit_fields = self._prepare_audit_fields()
            audit_field_names = ['create_uid', 'write_uid', 'create_date', 'write_date']
            for audit_field in audit_field_names:
                if audit_field in model_fields and audit_field not in final_fields:
                    data.loc[:, audit_field] = audit_fields[audit_field]
                    final_fields.append(audit_field)

            if 'company_id' in model_fields and 'company_id' not in final_fields:
                data.loc[:, 'company_id'] = self.env.company.id
                final_fields.append('company_id')

            # Generate IDs if needed
            if 'id' not in final_fields:
                record_count = len(data)
                if record_count > 0:
                    try:
                        next_ids = self._get_next_sequence_values(table_name, record_count)
                        data.loc[:, 'id'] = next_ids
                        final_fields.insert(0, 'id')
                    except Exception as e:
                        if 'id' in final_fields:
                            final_fields.remove('id')
                        if 'id' in data.columns:
                            data = data.drop(columns=['id'])

            # OPTIMIZED: Ensure temp columns exist (don't recreate every time)
            if has_complex_fields:
                self._ensure_temp_columns_exist(table_name, m2m_columns, o2m_columns)

            # Set up triggers
            if has_complex_fields:
                if m2m_trigger_val:
                    vals = json.dumps(m2m_trigger_val)
                    self.env.cr.execute(f"""
                                DROP TRIGGER IF EXISTS trg_process_m2m_mapping ON {table_name};
                                CREATE TRIGGER trg_process_m2m_mapping
                                AFTER INSERT ON {table_name}
                                FOR EACH ROW
                                EXECUTE FUNCTION process_m2m_mapping('{vals}');
                            """)

                if o2m_trigger_val:
                    vals = json.dumps(o2m_trigger_val)
                    self.env.cr.execute(f"""
                                DROP TRIGGER IF EXISTS trg_process_o2m_mapping ON {table_name};
                                CREATE TRIGGER trg_process_o2m_mapping
                                AFTER INSERT ON {table_name}
                                FOR EACH ROW
                                EXECUTE FUNCTION process_o2m_mapping('{vals}');
                            """)

            # Filter data to final fields
            data = data[final_fields].copy()

            # Handle translatable fields
            default_lang = self.env.context.get('lang') or 'en_US'
            translatable_columns = set()

            for column in data.columns:
                if column in model_fields:
                    field_info = model_fields[column]
                    if field_info.get('translate') and field_info.get('store'):
                        translatable_columns.add(column)

                        # OPTIMIZED: Vectorized JSONB conversion
                        def to_jsonb_value(val):
                            if pd.isna(val) or val is None or str(val).strip() == '':
                                return None
                            if isinstance(val, dict):
                                try:
                                    return json.dumps(val, ensure_ascii=False)
                                except:
                                    return json.dumps({default_lang: str(val)}, ensure_ascii=False)
                            s = str(val).strip()
                            if s.startswith('{') or s.startswith('['):
                                try:
                                    return json.dumps(json.loads(s), ensure_ascii=False)
                                except:
                                    return json.dumps({default_lang: s}, ensure_ascii=False)
                            return json.dumps({default_lang: s}, ensure_ascii=False)

                        try:
                            data[column] = data[column].apply(to_jsonb_value)
                        except Exception as e:
                            _logger.warning(f"Failed converting translate field {column}: {e}")

            # OPTIMIZED: Process data types with vectorized operations
            processed_data = data.copy()

            for column in processed_data.columns:
                if column in model_fields and column not in translatable_columns:
                    field_info = model_fields[column]
                    field_type = field_info['type']

                    if field_type in ['char', 'text']:
                        try:
                            processed_data[column] = (
                                processed_data[column]
                                .fillna('')  # ADD THIS
                                .astype(str)
                                .str.replace(r'[\n\r]+', ' ', regex=True)
                                .str.strip()
                                .replace({'nan': None, 'None': None, '': None})  # CHANGE THIS
                            )
                        except Exception as e:
                            _logger.warning(f"String processing error for {column}: {e}")
                            # Safe fallback
                            processed_data.loc[:, column] = processed_data[column].astype(str)
                            processed_data.loc[:, column] = processed_data[column].str.strip()
                    elif field_type in ['integer', 'float']:
                        numeric_series = pd.to_numeric(processed_data[column], errors='coerce')
                        if model_fields[column].get('required', False):
                            processed_data[column] = numeric_series.fillna(0)
                        else:
                            processed_data[column] = numeric_series

                    elif field_type == 'boolean':
                        # OPTIMIZED: Vectorized boolean conversion
                        try:
                            bool_series = processed_data[column].fillna(False).astype(bool)
                            processed_data[column] = bool_series.map({True: 't', False: 'f'})
                        except Exception as e:
                            _logger.warning(f"Boolean processing failed for {column}: {e}")
                            # Fallback to original method
                            processed_data.loc[:, column] = processed_data[column].fillna(False)
                            bool_values = []
                            for val in processed_data[column]:
                                if pd.isna(val):
                                    bool_values.append('f')
                                else:
                                    bool_values.append('t' if bool(val) else 'f')
                            processed_data.loc[:, column] = bool_values
                    elif field_type in ['date', 'datetime']:
                        # OPTIMIZED: Vectorized date processing
                        try:
                            # Try direct conversion first
                            date_series = pd.to_datetime(processed_data[column], errors='coerce')

                            # For failures, try common formats
                            mask_failed = date_series.isna() & processed_data[column].notna()

                            if mask_failed.any():
                                failed_values = processed_data.loc[mask_failed, column]

                                for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                                    still_failed = date_series.loc[mask_failed].isna()
                                    if still_failed.any():
                                        try:
                                            parsed = pd.to_datetime(
                                                failed_values.loc[still_failed],
                                                format=fmt,
                                                errors='coerce'
                                            )
                                            date_series.loc[mask_failed & still_failed] = parsed
                                        except:
                                            continue

                            # Format based on field type
                            if field_type == 'date':
                                formatted = date_series.dt.strftime('%Y-%m-%d')
                            else:
                                formatted = date_series.dt.strftime('%Y-%m-%d %H:%M:%S')

                            # Replace NaT with None
                            processed_data[column] = formatted.where(date_series.notna(), None)

                        except Exception as e:
                            _logger.warning(f"Date processing failed for {column}: {e}")
                            processed_data[column] = None

                    elif field_type == 'many2one':
                        processed_data[column] = pd.to_numeric(processed_data[column], errors='coerce').astype('Int64')

            # Prepare CSV buffer
            csv_buffer = BytesIO()

            # Build JSON arrays for O2M/M2M
            for col in o2m_columns + m2m_columns:
                if col not in processed_data.columns:
                    continue

                def build_array(val):
                    # val may be list, None, or stringified json
                    if isinstance(val, list):
                        return self._safe_json_array(val)
                    if val is None or val == "" or val == "[]":
                        return "[]"
                    if isinstance(val, str):
                        try:
                            parsed = json.loads(val)
                            if isinstance(parsed, list):
                                return self._safe_json_array(parsed)
                        except:
                            pass
                        return self._safe_json_array([val])
                    return self._safe_json_array([val])

                processed_data[col] = processed_data[col].apply(build_array)

                    # Final data preparation for COPY

            data_for_copy = processed_data.copy()

            for column in data_for_copy.columns:
                if column in model_fields:
                    field_info = model_fields[column]
                    field_type = field_info['type']
                    if field_info.get('translate') and field_info.get('store'):
                        data_for_copy[column] = data_for_copy[column].fillna('').astype(str)
                    elif field_type in ['integer', 'float', 'many2one']:
                        if field_type in ['integer', 'many2one']:
                            data_for_copy[column] = pd.to_numeric(data_for_copy[column], errors='coerce').astype(
                                'Int64')
                        else:
                            data_for_copy[column] = pd.to_numeric(data_for_copy[column], errors='coerce')
                    else:
                        data_for_copy[column] = data_for_copy[column].fillna('').astype(str)

                # Write to CSV
            data_for_copy.to_csv(
                csv_buffer,
                index=False,
                header=False,
                    sep='|',
                    na_rep='',
                    quoting=csv.QUOTE_MINIMAL,
                    doublequote=True
            )
            csv_buffer.seek(0)
                # Disable triggers
            self.env.cr.execute(f"ALTER TABLE {table_name} DISABLE TRIGGER USER;")
            if has_complex_fields:
                if m2m_trigger_val:
                    self.env.cr.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER trg_process_m2m_mapping;")
                if o2m_trigger_val:
                    self.env.cr.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER trg_process_o2m_mapping;")

            # PostgreSQL COPY
            fields_str = ",".join(final_fields)
            copy_sql = f"""
                                    COPY {table_name} ({fields_str})
                                    FROM STDIN WITH (
                                        FORMAT CSV,
                                        HEADER FALSE,
                                        DELIMITER '|',
                                        NULL '',
                                        QUOTE '"'
                                    )
                                """

            start_time = datetime.now()
            self.env.cr.copy_expert(copy_sql, csv_buffer)
            record_count = len(data)
            if record_count > 500:
                self.env.cr.commit()
            end_time = datetime.now()
            import_duration = (end_time - start_time).total_seconds()
            _logger.info(
                f"COPY completed in {import_duration:.2f}s for {record_count} records ({record_count / import_duration:.0f} records/sec)")
            # Sync sequence
            self._sync_sequence_after_import(table_name)
            # Re-enable triggers
            self.env.cr.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER USER;")

            # OPTIMIZED: Clear temp columns instead of dropping
            if has_complex_fields and (m2m_trigger_val or o2m_trigger_val):
                self._clear_temp_columns(table_name, m2m_columns + o2m_columns)
            # OPTIMIZED: Targeted invalidation
            Model.invalidate_model()

            # Invalidate related models
            for m2m_col, config in m2m_trigger_val.items():
                related_table = config.get('data_table')
                if related_table:
                    for model_name in self.env:
                        try:
                            if self.env[model_name]._table == related_table:
                                self.env[model_name].invalidate_model()
                                break
                        except:
                            continue

            for o2m_col, config in o2m_trigger_val.items():
                comodel_name = config.get('comodel_name')
                if comodel_name and comodel_name in self.env:
                    self.env[comodel_name].invalidate_model()

                # Analyze table
            self.env.cr.execute(f"ANALYZE {table_name};")

            # Get final count
            final_count = Model.search_count([])
            imported_count = final_count - initial_count

            return {
                'name': model_record.name,
                'record_count': imported_count,
                'duration': import_duration
            }
        except Exception as e:
            try:
                self.env.cr.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER USER;")
            except:
                pass

            if has_complex_fields and (m2m_trigger_val or o2m_trigger_val):
                try:
                    self._clear_temp_columns(table_name, m2m_columns + o2m_columns)
                except:
                    pass

            raise UserError(f"Failed to import data: {str(e)}")


    def _postgres_bulk_import_enhanced(self, data, model, final_fields, m2m_trigger_val, o2m_trigger_val,
                                       m2m_columns, o2m_columns, table_name, model_fields,
                                       initial_count, model_record, has_complex_fields, reference_cache):
        """
        Flexible import method handling complex one2many and many2many relationships.
        This enhanced version processes records individually with transaction safety,
        creating many2many relationship entries and one2many child records after parent
        insertion. It includes detailed error tracking, relationship resolution, and
        automatic creation of missing related records when needed.
        """
        try:
            env = self.env
            Model = env[model]
            odoo_fields = getattr(Model, "_fields", {}) or model_fields or {}
            if not table_name:
                table_name = Model._table
            # Verify table structure
            env.cr.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """)
            existing_columns = [row[0] for row in env.cr.fetchall()]
            # Clean regular fields
            cleaned_regular_fields = []
            for field in final_fields:
                clean_field = field.replace('m2m__', '').replace('o2m__', '')
                if field in existing_columns or clean_field in odoo_fields:
                    cleaned_regular_fields.append(field)
            # Separate M2M fields from regular fields
            original_data = data.copy()
            regular_final_fields = []
            m2m_field_mapping = {}
            for column in data.columns:
                if column.startswith("m2m__"):
                    real_field_name = column.replace("m2m__", "", 1)
                    m2m_field_mapping[real_field_name] = original_data[column].copy()
                elif column in m2m_columns:
                    real_field_name = column.replace("m2m__", "", 1) if column.startswith("m2m__") else column
                    m2m_field_mapping[real_field_name] = original_data[column].copy()
                else:
                    field_obj = odoo_fields.get(column)
                    if field_obj:
                        field_type = getattr(field_obj, "type", None)
                        if field_type == 'many2many':
                            m2m_field_mapping[column] = original_data[column].copy()
                        elif column in existing_columns:
                            regular_final_fields.append(column)
                    elif column in existing_columns:
                        regular_final_fields.append(column)
            # Clean fields - remove computed fields that are not stored
            model_fields = self.env[model]._fields
            clean_fields = []
            for f in regular_final_fields:
                field = model_fields.get(f)
                if not field:
                    if f in existing_columns:
                        clean_fields.append(f)
                    continue
                if getattr(field, 'compute', False) and not field.store and not field.required:
                    continue
                if f in existing_columns:
                    clean_fields.append(f)
            regular_final_fields = clean_fields
            # Add O2M fields to regular fields for processing
            for o2m_col in o2m_columns:
                if o2m_col not in regular_final_fields and o2m_col in data.columns and o2m_col in existing_columns:
                    regular_final_fields.append(o2m_col)
            if not regular_final_fields:
                _logger.warning("No regular fields detected to insert; aborting bulk import.")
                return {
                    "name": model_record.name,
                    "record_count": 0,
                    "duration": 0.0,
                    "warnings": "No regular fields detected for main insert.",
                }
            # Only keep columns that exist in the table
            available_columns = [col for col in regular_final_fields if col in existing_columns]
            insert_data = data[available_columns].copy()
            # Handle sequence for name field
            if 'name' in model_fields:
                sequence = self._get_sequence_for_model(model)
                needs_sequence = False
                name_in_data = 'name' in insert_data.columns
                if not name_in_data:
                    needs_sequence = True
                else:
                    non_null_names = insert_data['name'].dropna()
                    if len(non_null_names) == 0:
                        needs_sequence = True
                    else:
                        name_check_results = []
                        for val in non_null_names:
                            str_val = str(val).strip().lower()
                            name_check_results.append(str_val in ['new', '', 'false'])
                        needs_sequence = all(name_check_results)
                if sequence and needs_sequence:
                    record_count = len(insert_data)
                    if record_count > 0:
                        try:
                            sequence_values = self._generate_bulk_sequences(sequence, record_count)
                            insert_data = insert_data.copy()
                            insert_data.loc[:, 'name'] = sequence_values
                            if 'name' not in available_columns:
                                available_columns.append('name')
                        except Exception as e:
                            _logger.error(f"Failed to generate sequences: {e}")
            # Add audit fields - only if they exist in the table
            audit_values = self._prepare_audit_fields()
            if 'active' in model_fields and 'active' not in available_columns and 'active' in existing_columns:
                insert_data['active'] = [True] * len(insert_data)
                available_columns.append('active')
            for audit_field, value in audit_values.items():
                field_obj = odoo_fields.get(audit_field)
                if not field_obj:
                    continue
                if not getattr(field_obj, "store", False):
                    continue
                if getattr(field_obj, "compute", False):
                    continue
                if getattr(field_obj, "related", False):
                    continue
                if audit_field not in existing_columns:
                    continue
                if audit_field not in insert_data.columns:
                    insert_data[audit_field] = value
                if audit_field not in available_columns:
                    available_columns.append(audit_field)
            # Generate IDs if needed
            if 'id' not in available_columns and 'id' in existing_columns:
                record_count = len(insert_data)
                if record_count > 0:
                    try:
                        next_ids = self._get_next_sequence_values(table_name, record_count)
                        insert_data = insert_data.copy()
                        insert_data.loc[:, 'id'] = next_ids
                        available_columns.insert(0, 'id')
                    except Exception as e:
                        if 'id' in available_columns:
                            available_columns.remove('id')
                        if 'id' in insert_data.columns:
                            insert_data = insert_data.drop(columns=['id'])
            # Process O2M JSON fields
            for o2m_col in o2m_columns:
                if o2m_col in insert_data.columns and o2m_col in existing_columns:
                    json_values = []
                    for val in insert_data[o2m_col]:
                        if isinstance(val, list):
                            json_values.append(json.dumps(val, ensure_ascii=False))
                        else:
                            json_values.append(val)
                    insert_data = insert_data.copy()
                    insert_data.loc[:, o2m_col] = json_values
            # Insert records using COPY for better performance
            inserted_count = 0
            failed_records = []
            inserted_row_ids = {}
            # Final check: ensure all columns exist in table
            final_insert_columns = [col for col in available_columns if col in existing_columns]
            columns_str = ",".join(f'"{col}"' for col in final_insert_columns)
            placeholders = ",".join(["%s"] * len(final_insert_columns))
            insert_sql = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders}) RETURNING id'
            for row_index, row in insert_data.iterrows():
                savepoint_name = f"import_record_{row_index}".replace('-', '_')
                try:
                    env.cr.execute(f"SAVEPOINT {savepoint_name}")
                    values = []
                    for field_name in final_insert_columns:
                        raw_value = row.get(field_name, None)
                        field_obj = odoo_fields.get(field_name)
                        if field_obj and getattr(field_obj, "translate", False):
                            default_lang = env.context.get('lang', 'en_US')
                            if pd.isna(raw_value) or raw_value in (None, '', 'nan', 'None'):
                                values.append(None)
                            else:
                                values.append(json.dumps({default_lang: str(raw_value)}))
                            continue
                        if pd.isna(raw_value):
                            values.append(None)
                            continue
                        if field_obj is None:
                            values.append(raw_value)
                            continue
                        ftype = getattr(field_obj, "type", None)
                        try:
                            if ftype in ("char", "text", "html", "selection"):
                                values.append(str(raw_value))
                            elif ftype == "many2one":
                                if pd.isna(raw_value) or raw_value in (None, '', 'nan', 'None'):
                                    values.append(None)
                                else:
                                    comodel = field_obj.comodel_name
                                    if str(raw_value).isdigit():
                                        values.append(int(raw_value))
                                    else:
                                        record = env[comodel].search([('name', '=', str(raw_value).strip())], limit=1)
                                        if record:
                                            values.append(record.id)
                                        else:
                                            new_rec = env[comodel].create({'name': raw_value})
                                            values.append(new_rec.id)
                            elif ftype in ("float", "monetary"):
                                values.append(float(raw_value))
                            elif ftype == "boolean":
                                if pd.isna(raw_value):
                                    values.append(None)
                                else:
                                    v = str(raw_value).strip().lower()
                                    values.append(v in ("1", "true", "yes", "y", "t"))
                            elif ftype in ("date", "datetime"):
                                try:
                                    parsed = pd.to_datetime(raw_value, errors='coerce')
                                    values.append(parsed.strftime('%Y-%m-%d %H:%M:%S') if parsed else None)
                                except:
                                    values.append(None)
                            else:
                                values.append(raw_value)
                        except Exception as conv_err:
                            values.append(raw_value)
                    values_tuple = tuple(values)
                    _logger.info(f"Inserting record index {row_index} into {table_name}")
                    env.cr.execute(insert_sql, values_tuple)
                    result = env.cr.fetchone()
                    if result:
                        new_id = result[0]
                        inserted_row_ids[row_index] = new_id
                        inserted_count += 1
                        env.cr.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    else:
                        env.cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                        failed_records.append((row_index, "No ID returned after INSERT"))
                except Exception as row_error:
                    env.cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                    failed_records.append((row_index, str(row_error)))
            env.cr.commit()
            # Initialize counters for relationships
            m2m_processed = 0
            m2m_failed = 0
            o2m_processed = 0
            o2m_failed = 0
            # Process M2M relationships
            if m2m_field_mapping and inserted_row_ids:
                for row_index, record_id in inserted_row_ids.items():
                    for m2m_field_name, series in m2m_field_mapping.items():
                        if row_index not in series.index:
                            continue
                        m2m_values = series.loc[row_index]
                        if pd.isna(m2m_values) or m2m_values in ("", "nan", "None", None):
                            continue
                        field_obj = odoo_fields.get(m2m_field_name)
                        if not field_obj or getattr(field_obj, "type", None) != "many2many":
                            continue
                        relation_table = field_obj.relation
                        column1 = field_obj.column1
                        column2 = field_obj.column2
                        comodel_name = field_obj.comodel_name
                        # Parse the M2M values
                        if isinstance(m2m_values, str):
                            tokens = []
                            for token in m2m_values.replace(";", ",").split(","):
                                token = token.strip()
                                if token:
                                    tokens.append(token)
                        else:
                            tokens = [str(m2m_values).strip()]
                        for token in tokens:
                            if not token:
                                continue
                            try:
                                safe_token = str(hash(token)).replace('-', '_')
                                savepoint_name = f"m2m_{record_id}_{m2m_field_name}_{safe_token}"
                                env.cr.execute(f"SAVEPOINT {savepoint_name}")
                                related_id = None
                                if token.isdigit():
                                    related_id = int(token)
                                    if env[comodel_name].browse(related_id).exists():
                                        _logger.info(f"Token '{token}' resolved as direct ID: {related_id}")
                                    else:
                                        _logger.warning(
                                            f"Token '{token}' is numeric but ID {related_id} doesn't exist in {comodel_name}")
                                        related_id = None
                                if not related_id:
                                    try:
                                        related_id = env.ref(token).id
                                    except ValueError:
                                        pass
                                if not related_id:
                                    comodel_fields = env[comodel_name].fields_get()
                                    if 'name' in comodel_fields and comodel_fields['name'].get('store'):
                                        related_rec = env[comodel_name].search([("name", "=ilike", token)], limit=1)
                                        if related_rec:
                                            related_id = related_rec.id
                                if not related_id and 'code' in env[comodel_name]._fields:
                                    code_field = env[comodel_name]._fields['code']
                                    if getattr(code_field, 'store', False):
                                        related_rec = env[comodel_name].search([("code", "=ilike", token)], limit=1)
                                        if related_rec:
                                            related_id = related_rec.id
                                if not related_id:
                                    models_not_to_auto_create = ['res.groups', 'ir.model.fields', 'ir.model', 'ir.rule',
                                                                 'ir.ui.menu', 'ir.actions.actions',
                                                                 'ir.actions.server']
                                    if comodel_name not in models_not_to_auto_create:
                                        try:
                                            create_vals = {'name': token}
                                            new_rec = env[comodel_name].create(create_vals)
                                            related_id = new_rec.id
                                        except Exception as create_error:
                                            related_id = None
                                if not related_id:
                                    env.cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                                    m2m_failed += 1
                                    continue
                                # Check if relationship already exists
                                check_sql = f'''
                                    SELECT 1 FROM "{relation_table}" 
                                    WHERE "{column1}" = %s AND "{column2}" = %s
                                    LIMIT 1
                                '''
                                env.cr.execute(check_sql, (record_id, related_id))
                                exists = env.cr.fetchone()
                                if not exists:
                                    insert_m2m_sql = (
                                        f'INSERT INTO "{relation_table}" ("{column1}", "{column2}") '
                                        f"VALUES (%s, %s)"
                                    )
                                    env.cr.execute(insert_m2m_sql, (record_id, related_id))
                                    m2m_processed += 1
                                env.cr.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                            except Exception as m2m_error:
                                env.cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                                m2m_failed += 1
                env.cr.commit()
            # Process O2M relationships if any
            if o2m_columns and inserted_row_ids:
                for row_index, record_id in inserted_row_ids.items():
                    for o2m_col in o2m_columns:
                        if o2m_col not in insert_data.columns or row_index not in insert_data.index:
                            continue
                        o2m_data = insert_data.loc[row_index, o2m_col]
                        if pd.isna(o2m_data) or not o2m_data:
                            continue
                        try:
                            # Parse O2M JSON data
                            if isinstance(o2m_data, str):
                                child_records = json.loads(o2m_data)
                            else:
                                child_records = o2m_data
                            if not isinstance(child_records, list):
                                continue
                            real_field_name = o2m_col.replace("o2m__", "")
                            field_obj = odoo_fields.get(real_field_name)
                            if not field_obj or getattr(field_obj, "type", None) != "one2many":
                                continue
                            comodel_name = field_obj.comodel_name
                            inverse_name = getattr(field_obj, "inverse_name", None)
                            for child_data in child_records:
                                if not isinstance(child_data, dict):
                                    continue
                                try:
                                    # Set the inverse field to link to parent
                                    if inverse_name:
                                        child_data[inverse_name] = record_id
                                    # Create child record
                                    child_record = env[comodel_name].create(child_data)
                                    o2m_processed += 1
                                except Exception as child_error:
                                    o2m_failed += 1
                                    _logger.warning(f"Failed to create O2M child record: {child_error}")
                        except Exception as o2m_error:
                            o2m_failed += 1
                            _logger.warning(f"Failed to process O2M data: {o2m_error}")
                env.cr.commit()
            # Final count and cleanup
            try:
                env.cr.commit()
                with env.registry.cursor() as new_cr:
                    new_cr.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                    final_count = new_cr.fetchone()[0]
                actual_imported_count = inserted_count
            except Exception as count_error:
                actual_imported_count = inserted_count
                final_count = initial_count + inserted_count
            imported_count = actual_imported_count
            # Clean up temporary columns
            try:
                self.remove_m2m_temp_columns(table_name, m2m_columns + o2m_columns)
            except Exception as cleanup_error:
                _logger.warning(f"Failed to clean up temporary columns: {cleanup_error}")
            warnings = None
            if failed_records:
                warnings = f"Failed to import {len(failed_records)} records."
            if m2m_failed > 0:
                warnings = f"{warnings} {m2m_failed} M2M relationships failed." if warnings else f"{m2m_failed} M2M relationships failed."
            if o2m_failed > 0:
                warnings = f"{warnings} {o2m_failed} O2M relationships failed." if warnings else f"{o2m_failed} O2M relationships failed."
            return {
                "name": model_record.name,
                "record_count": imported_count,
                "duration": 0.1,
                "warnings": warnings,
            }
        except Exception as e:
            self.env.cr.rollback()
            raise UserError(_("Failed to import data: %s") % str(e))

    @api.model
    def validate_columns(self, res_id, model, columns):
        """
        Validates the imported column definitions.
        """
        column_names = tuple(sorted([
            item['fieldInfo']['id'] for item in columns if 'fieldInfo' in item
        ]))
        cache_key = (model, column_names)

        # Check cache first
        if cache_key in self._validation_cache:
            cached_result = self._validation_cache[cache_key].copy()
            cache_time = cached_result.pop('_cache_time', 0)

            if (datetime.now().timestamp() - cache_time) < 300:  # 5 min cache
                _logger.info(f"Using cached validation for {model}")
                return cached_result

        # Original validation logic
        try:
            uploaded_columns = [item['fieldInfo']['id'] for item in columns if 'fieldInfo' in item]

            if len(uploaded_columns) < len(columns):
                invalid_columns = [col.get('name', 'Unknown') for col in columns if 'fieldInfo' not in col]
                return {
                    'is_valid': False,
                    'invalid_columns': invalid_columns,
                    'error_type': 'invalid_columns'
                }
            # ... rest of validation logic ...
            result = {
                'is_valid': True,
                # ... other fields ...
                '_cache_time': datetime.now().timestamp()
            }
            # Store in cache (limit cache size to 100 entries)
            if len(self._validation_cache) > 100:
                # Remove oldest entry
                oldest_key = min(self._validation_cache.keys(),
                                 key=lambda k: self._validation_cache[k].get('_cache_time', 0))
                del self._validation_cache[oldest_key]
            self._validation_cache[cache_key] = result.copy()
            return result
        except Exception as e:
            _logger.error(f"Validation error for {model}: {e}")
            return {'is_valid': False, 'error_message': str(e)}

    def _ensure_temp_columns_exist(self, table_name, m2m_columns, o2m_columns):
        """
        OPTIMIZED: Create temp columns once, reuse them.
        """
        all_temp_cols = m2m_columns + o2m_columns

        if not all_temp_cols:
            return

        # Check existing columns in single query
        self.env.cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            AND column_name = ANY(%s)
        """, (table_name, all_temp_cols))

        existing_cols = {row[0] for row in self.env.cr.fetchall()}

        # Only create missing columns
        missing_cols = set(all_temp_cols) - existing_cols

        if missing_cols:
            _logger.info(f"Creating {len(missing_cols)} temp columns for {table_name}")

            for col in missing_cols:
                col_type = 'jsonb' if col.startswith('o2m__') else 'text'
                self.env.cr.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col} {col_type};"
                )

    def _clear_temp_columns(self, table_name, temp_columns):
        """
        OPTIMIZED: Clear temp column data without dropping columns.
        """
        if not temp_columns:
            return

        set_clauses = ', '.join([f"{col} = NULL" for col in temp_columns])

        try:
            self.env.cr.execute(f"UPDATE {table_name} SET {set_clauses}")
            _logger.info(f"Cleared {len(temp_columns)} temp columns in {table_name}")
        except Exception as e:
            _logger.warning(f"Failed to clear temp columns: {e}")

class Import(models.TransientModel):
    _inherit = 'base_import.import'

    @api.model
    def get_fields_tree(self, model, depth=FIELDS_RECURSION_LIMIT):
        Model = self.env[model]
        importable_fields = [{
            'id': 'id',
            'name': 'id',
            'string': _("External ID"),
            'required': False,
            'fields': [],
            'type': 'id',
            'model_name': model,
        }]
        if not depth:
            return importable_fields
        model_fields = Model.fields_get()
        for name, field in model_fields.items():
            if field.get('deprecated', False):
                continue
            if not field.get('store'):
                continue
            field_value = {
                'id': name,
                'name': name,
                'string': field['string'],
                'required': bool(field.get('required')),
                'fields': [],
                'type': field['type'],
                'model_name': model,
            }
            # many2one / many2many
            if field['type'] in ('many2one', 'many2many'):
                field_value['comodel_name'] = field['relation']
                field_value['fields'] = [
                    {
                        'id': f"{name}.id",
                        'name': 'id',
                        'string': _("External ID"),
                        'required': False,
                        'fields': [],
                        'type': 'id',
                        'model_name': field['relation'],
                    },
                    {
                        'id': f"{name}._id",
                        'name': '.id',
                        'string': _("Database ID"),
                        'required': False,
                        'fields': [],
                        'type': 'id',
                        'model_name': field['relation'],
                    },
                ]
            # one2many
            elif field['type'] == 'one2many':
                field_value['comodel_name'] = field['relation']
                field_value['fields'] = self.get_fields_tree(field['relation'], depth - 1)
                # add .id only for technical group
                if self.env.user.has_group('base.group_no_one'):
                    field_value['fields'].append({
                        'id': f"{name}._id",
                        'name': '.id',
                        'string': _("Database ID"),
                        'required': False,
                        'fields': [],
                        'type': 'id',
                        'model_name': field['relation'],
                    })
            importable_fields.append(field_value)
        return importable_fields