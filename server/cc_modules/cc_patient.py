#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import datetime
import dateutil.relativedelta

import pythonlib.rnc_db as rnc_db
import pythonlib.rnc_web as ws

from cc_audit import audit
from cc_constants import (
    ACTION,
    DATEFORMAT,
    ERA_NOW,
    NUMBER_OF_IDNUMS,
    PARAM,
    STANDARD_GENERIC_FIELDSPECS
)
import cc_db
import cc_dt
import cc_hl7
import cc_html
import cc_namedtuples
from cc_pls import pls
import cc_policy
import cc_report
import cc_specialnote
from cc_unittest import unit_test_ignore
import cc_xml


# =============================================================================
# Patient class
# =============================================================================

class Patient:
    """Class representing a patient."""
    TABLENAME = "patient"
    FIELDSPECS = STANDARD_GENERIC_FIELDSPECS + [
        dict(name="id", cctype="INT_UNSIGNED", notnull=True,
             comment="Primary key (patient ID) on the source tablet device"),
        # ... client PK
        dict(name="forename", cctype="PATIENTNAME",
             comment="Forename", indexed=True, index_nchar=10,
             identifies_patient=True,
             cris_include=True),
        dict(name="surname", cctype="PATIENTNAME",
             comment="Surname", indexed=True, index_nchar=10,
             identifies_patient=True,
             cris_include=True),
        dict(name="dob", cctype="ISO8601",
             comment="Date of birth", indexed=True, index_nchar=10,
             identifies_patient=True,
             cris_include=True),
        # ... e.g. "2013-02-04"
        dict(name="sex", cctype="SEX",
             comment="Sex (M, F, X)", indexed=True,
             cris_include=True),
        dict(name="address", cctype="TEXT",
             comment="Address", identifies_patient=True),
        dict(name="gp", cctype="TEXT",
             comment="General practitioner (GP)"),
        dict(name="other", cctype="TEXT",
             comment="Other details", identifies_patient=True),
    ]
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        nstr = str(n)
        FIELDSPECS.append(dict(name="idnum" + nstr,
                               cctype="BIGINT_UNSIGNED",
                               indexed=True,
                               comment="ID number " + nstr,
                               cris_include=True))
        FIELDSPECS.append(dict(name="iddesc" + nstr,
                               cctype="IDDESCRIPTOR",
                               comment="ID description " + nstr,
                               anon=True,
                               cris_include=True))
        FIELDSPECS.append(dict(name="idshortdesc" + nstr,
                               cctype="IDDESCRIPTOR",
                               comment="ID short description " + nstr,
                               anon=True,
                               cris_include=True))

    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns=False):
        """Make underlying database tables."""
        cc_db.create_standard_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def __init__(self, serverpk=None):
        """Initialize, loading from database."""
        pls.db.fetch_object_from_db_by_pk(self, Patient.TABLENAME,
                                          Patient.FIELDS, serverpk)
        # Don't load special notes, for speed (retrieved on demand)
        self._special_notes = None

    def get_xml_root(self, skip_fields=[]):
        """Get root of XML tree, as an XmlElementTuple."""
        branches = cc_xml.make_xml_branches_from_fieldspecs(
            self, self.FIELDSPECS, skip_fields=skip_fields)
        # Special notes
        self.ensure_special_notes_loaded()
        branches.append(cc_xml.XML_COMMENT_SPECIAL_NOTES)
        for sn in self._special_notes:
            branches.append(sn.get_xml_root())
        return cc_namedtuples.XmlElementTuple(name=self.TABLENAME,
                                              value=branches)

    def anonymise(self):
        """Wipes the object's patient-identifiable content.
        Does NOT write to database."""
        # Save temporarily
        sex = self.sex
        dob = self.get_dob()
        # Wipe
        rnc_db.blank_object(self, Patient.FIELDS)
        # Replace selected values
        self.sex = sex
        if dob:
            dob = dob.replace(day=1)  # set DOB to first of the month
            self.dob = cc_dt.format_datetime(dob,
                                             DATEFORMAT.ISO8601_DATE_ONLY)

    def get_literals_for_anonymisation(self):
        """Return a list of strings that require removing from other fields in
        the anonymisation process."""
        address = self.address or ""  # get rid of None values
        other = self.other or ""
        return (
            [
                self.forename,
                self.surname,
            ]
            + address.split(",")
            + other.split(",")
            + self.get_idnum_array()
        )

    def get_dates_for_anonymisation(self):
        """Return a list of dates/datetimes that require removing from other
        fields in the anonymisation process."""
        return [
            self.get_dob(),
        ]

    def get_bare_ptinfo(self):
        """Get basic identifying information, as a BarePatientInfo."""
        return cc_namedtuples.BarePatientInfo(
            forename=self.forename,
            surname=self.surname,
            dob=self.dob,
            sex=self.sex,
            idnum_array=self.get_idnum_array()
        )

    def get_idnum_array(self):
        """Return array (length NUMBER_OF_IDNUMS) containing ID numbers."""
        arr = []
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            arr.append(self.get_idnum(n))
        return arr

    def get_idshortdesc_array(self):
        """Return array (length NUMBER_OF_IDNUMS) containing ID short
        descriptions."""
        arr = []
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            arr.append(self.get_idshortdesc(n))
        return arr

    def satisfies_upload_id_policy(self):
        """Does the patient satisfy the uploading ID policy?"""
        return cc_policy.satisfies_upload_id_policy(self.get_bare_ptinfo())

    def satisfies_finalize_id_policy(self):
        """Does the patient satisfy the finalizing ID policy?"""
        return cc_policy.satisfies_finalize_id_policy(self.get_bare_ptinfo())

    def satisfies_id_policy(self, policy):
        """Does the patient satisfy a particular ID policy?"""
        return cc_policy.satisfies_id_policy(policy, self.get_bare_ptinfo())

    def dump(self):
        """Dump object to database's logger."""
        rnc_db.dump_database_object(self, Patient.FIELDS)

    def get_surname(self):
        """Get surname (in upper case) or ""."""
        return self.surname.upper() if self.surname else ""

    def get_forename(self):
        """Get forename (in upper case) or ""."""
        return self.forename.upper() if self.forename else ""

    def get_surname_forename_upper(self):
        """Get "SURNAME, FORENAME" in HTML-safe format, using "UNKNOWN" for
        missing details."""
        s = self.surname.upper() if self.surname else "(UNKNOWN)"
        f = self.forename.upper() if self.surname else "(UNKNOWN)"
        return ws.webify(s + ", " + f)

    def get_dob_html(self, longform):
        """HTML fragment for date of birth."""
        if longform:
            return "<br>Date of birth: {}".format(
                cc_html.answer(cc_dt.format_datetime_string(
                    self.dob, DATEFORMAT.LONG_DATE, default=None)))
        return "DOB: {}.".format(cc_dt.format_datetime_string(
            self.dob, DATEFORMAT.SHORT_DATE))

    def get_age(self, default=""):
        """Age (in whole years) today, or default."""
        return self.get_age_at(pls.TODAY, default=default)

    def get_dob(self):
        """Date of birth, as a a timezone-naive date."""
        if self.dob is None:
            return None
        return cc_dt.get_date_from_string(self.dob)

    def get_age_at(self, when, default=""):
        """Age (in whole years) at a particular date, or default.

        Args:
            when: date or datetime
        """
        dob = self.get_dob()  # date; timezone-naive
        if dob is None:
            return default
        # when must be a date, i.e. timezone-naive. So:
        if type(when) is datetime.datetime:
            when = when.date()
        # if it wasn't timezone-naive, we could make it timezone-naive: e.g.
        # now = now.replace(tzinfo = None)
        return dateutil.relativedelta.relativedelta(when, dob).years

    def get_age_at_string(self, now_string, default=""):
        """Age (in whole years) at a particular date, or default.

        Args:
            now_string: date/time in string format, e.g. ISO-8601
        """
        if now_string is None:
            return default
        return self.get_age_at(cc_dt.get_datetime_from_string(now_string))

    def is_female(self):
        """Is sex 'F'?"""
        return self.sex == "F"

    def is_male(self):
        """Is sex 'M'?"""
        return self.sex == "M"

    def get_sex(self):
        """Return sex or ""."""
        return "" if not self.sex else self.sex

    def get_sex_verbose(self, default="sex unknown"):
        """Returns HTML-safe version of sex, or default."""
        return default if not self.sex else ws.webify(self.sex)

    def get_address(self):
        """Returns address (NOT necessarily web-safe)."""
        return self.address

    def get_hl7_pid_segment(self, recipient_def):
        """Get HL7 patient identifier (PID) segment."""
        # Put the primary one first:
        patient_id_tuple_list = [
            cc_namedtuples.PatientIdentifierTuple(
                id=str(self.get_idnum(recipient_def.primary_idnum)),
                id_type=recipient_def.get_id_type(
                    recipient_def.primary_idnum),
                assigning_authority=recipient_def.get_id_aa(
                    recipient_def.primary_idnum)
            )
        ]
        # Then the rest:
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            if n == recipient_def.primary_idnum:
                continue
            idnum = self.get_idnum(n)
            if idnum is None:
                continue
            patient_id_tuple_list.append(
                cc_namedtuples.PatientIdentifierTuple(
                    id=str(idnum),
                    id_type=recipient_def.get_id_type(n),
                    assigning_authority=recipient_def.get_id_aa(n)
                )
            )
        return cc_hl7.make_pid_segment(
            forename=self.get_surname(),
            surname=self.get_forename(),
            dob=self.get_dob(),
            sex=self.get_sex(),
            address=self.get_address(),
            patient_id_tuple_list=patient_id_tuple_list,
        )

    def get_idnum(self, idnum):
        """Get value of a specific ID number.

        Args:
            idnum: integer from 1 to NUMBER_OF_IDNUMS inclusive
        """
        if idnum < 1 or idnum > NUMBER_OF_IDNUMS:
            return None
        nstr = str(idnum)
        return getattr(self, "idnum" + nstr)

    def get_iddesc(self, n):
        """Get value of a specific ID description.

        Args:
            idnum: integer from 1 to NUMBER_OF_IDNUMS inclusive
        """
        if n < 1 or n > NUMBER_OF_IDNUMS:
            return None
        return getattr(self, "iddesc" + str(n))

    def get_idshortdesc(self, n):
        """Get value of a specific ID short description.

        Args:
            idnum: integer from 1 to NUMBER_OF_IDNUMS inclusive
        """
        if n < 1 or n > NUMBER_OF_IDNUMS:
            return None
        return getattr(self, "idshortdesc" + str(n))

    def get_id_generic(self, longform, idnum, desc, shortdesc, serverdesc,
                       servershortdesc, idnumtext, label_id_numbers=False):
        """Returns (conflict, description).

        Gets ID description/number in HTML format, or "", plus conflict
        information.

        Args:
            longform: verbose (for most HTML) or not (for PDF headers)
            idnum: value of ID number
            desc: description
            shortdesc: short description:
            serverdesc: server's description
            servershortdesc: server's short description
            idnumtext: string used as a prefix if label_id_numbers
            label_id_numbers: whether to use prefix

        In practice:
            longform=False: used in PDF headers
            longform=True, label_id_numbers=True: used in trackers
            longform=True, label_id_numbers=False: used in tasks

        Returns (conflict, description).
            conflict: Boolean; server's description doesn't match patient's
            description: HTML
        """
        if idnum is None:
            return False, ""  # no conflict if no number!
        prefix = u"<i>(" + idnumtext + u")</i> " if label_id_numbers else ""
        if longform:
            conflict = (desc != serverdesc)
            if conflict:
                finaldesc = u"{} [server] or {} [tablet]".format(serverdesc,
                                                                 desc)
            else:
                finaldesc = ws.webify(desc)
            return conflict, u"<br>{}{}: <b>{}</b>".format(
                prefix,
                finaldesc,
                idnum
            )
        else:
            conflict = (shortdesc != servershortdesc)
            if conflict:
                finaldesc = "{} [server] or {} [tablet]".format(
                    servershortdesc, shortdesc)
            else:
                finaldesc = ws.webify(shortdesc)
            return conflict, "{}{}: {}.".format(
                prefix,
                finaldesc,
                idnum
            )

    def get_idnum_conflict_and_html(self, n, longform, label_id_numbers=False):
        """Returns (conflict, description HTML).

        Args:
            n: which ID number? From 1 to NUMBER_OF_IDNUMS inclusive.
            longform: see get_id_generic
        """
        if n < 1 or n > NUMBER_OF_IDNUMS:
            return False, "Invalid ID number: {}".format(n)
        nstr = str(n)  # which ID number?
        return self.get_id_generic(
            longform,
            getattr(self, "idnum" + nstr),
            getattr(self, "iddesc" + nstr),
            getattr(self, "idshortdesc" + nstr),
            pls.get_id_desc(n),
            pls.get_id_shortdesc(n),
            "idnum" + nstr,
            label_id_numbers
        )

    def get_idother_html(self, longform):
        """Get HTML for 'other' information."""
        if not self.other:
            return ""
        if longform:
            return "<br>Other details: <b>{}</b>".format(ws.webify(self.other))
        return ws.webify(self.other)

    def get_gp_html(self, longform):
        """Get HTML for general practitioner details."""
        if not self.gp:
            return ""
        if longform:
            return "<br>GP: <b>{}</b>".format(ws.webify(self.gp))
        return ws.webify(self.gp)

    def get_address_html(self, longform):
        """Get HTML for address details."""
        if not self.address:
            return ""
        if longform:
            return "<br>Address: <b>{}</b>".format(ws.webify(self.address))
        return ws.webify(self.address)

    def get_html_for_page_header(self):
        """Get HTML used for PDF page header."""
        h = u"<b>{}</b> ({}). {}".format(
            self.get_surname_forename_upper(),
            self.get_sex_verbose(),
            self.get_dob_html(False),
        )
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            conflict, msg = self.get_idnum_conflict_and_html(n, False)
            h += " " + msg
        h += " " + self.get_idother_html(False)
        return h

    def get_html_for_task_header(self, label_id_numbers=False):
        """Get HTML used for patient details in tasks."""
        h = u"""
            <div class="patient">
                <b>{name}</b> ({sex})
                {dob}
        """.format(
            name=self.get_surname_forename_upper(),
            sex=self.get_sex_verbose(),
            dob=self.get_dob_html(True),
        )
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            conflict, msg = self.get_idnum_conflict_and_html(n, True,
                                                             label_id_numbers)
            h += u"""
                {} <!-- ID{} -->
            """.format(
                msg,
                n
            )
        h += u"""
                {} <!-- ID_other -->
                {} <!-- address -->
                {} <!-- GP -->
            </div>
        """.format(
            self.get_idother_html(True),
            self.get_address_html(True),
            self.get_gp_html(True),
        )
        h += self.get_special_notes()
        return h

    def get_html_for_webview_patient_column(self):
        """Get HTML for patient details in task summary view."""
        return u"""
            <b>{}</b> ({}, {}, aged {})
        """.format(
            self.get_surname_forename_upper(),
            self.get_sex_verbose(),
            cc_dt.format_datetime_string(self.dob, DATEFORMAT.SHORT_DATE,
                                         default="?"),
            self.get_age(default="?"),
        )

    def get_conflict_html_for_id_col(self):
        """Returns (conflict, html) used for patient ID column in task summary
        view."""
        h = u""
        conflict = False
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            c, msg = self.get_idnum_conflict_and_html(n, False)
            conflict = conflict or c
            h += " " + msg
        h += " " + self.get_idother_html(False)
        return conflict, h

    def get_url_edit_patient(self):
        url = cc_html.get_generic_action_url(ACTION.EDIT_PATIENT)
        url += cc_html.get_url_field_value_pair(PARAM.SERVERPK, self._pk)
        return url

    def is_preserved(self):
        """Is the patient record preserved and erased from the tablet?"""
        return (self._pk is not None and self._era != ERA_NOW)

    def save(self):
        """Saves patient record back to database. UNUSUAL."""
        if self._pk is None:
            return
        pls.db.update_object_in_db(self, Patient.TABLENAME, Patient.FIELDS)

    # -------------------------------------------------------------------------
    # Audit
    # -------------------------------------------------------------------------

    def audit(self, details, from_console=False):
        """Audits actions to this patient."""
        audit(details,
              patient_server_pk=self._pk,
              table=Patient.TABLENAME,
              server_pk=self._pk,
              from_console=from_console)

    # -------------------------------------------------------------------------
    # Special notes
    # -------------------------------------------------------------------------

    def ensure_special_notes_loaded(self):
        if self._special_notes is None:
            self.load_special_notes()

    def load_special_notes(self):
        self._special_notes = cc_specialnote.SpecialNote.get_all_instances(
            Patient.TABLENAME, self.id, self._device, self._era)
        # Will now be a list (though possibly an empty one).

    def apply_special_note(self, note, user, from_console=False,
                           audit_msg="Special note applied manually"):
        """Manually applies a special note to a patient.
        WRITES TO DATABASE.
        """
        sn = cc_specialnote.SpecialNote()
        sn.basetable = Patient.TABLENAME
        sn.task_id = self.id
        sn.device = self._device
        sn.era = self._era
        sn.note_at = cc_dt.format_datetime(pls.NOW_LOCAL_TZ,
                                           DATEFORMAT.ISO8601)
        sn.user = user
        sn.note = note
        sn.save()
        self.audit(audit_msg, from_console)
        # HL7 deletion of corresponding tasks is done in camcops.py
        self._special_notes = None   # will be reloaded if needed

    def get_special_notes(self):
        self.ensure_special_notes_loaded()
        if not self._special_notes:
            return ""
        note_html = u"<br>".join([
            x.get_note_as_html() for x in self._special_notes])
        return u"""
            <div class="specialnote">
                <b>PATIENT SPECIAL NOTES:</b><br>
                {}
            </div>
        """.format(
            note_html
        )


# =============================================================================
# Database lookup
# =============================================================================

def get_current_version_of_patient_by_client_info(device, clientpk, era):
    """Returns current Patient object, or None."""
    serverpk = cc_db.get_current_server_pk_by_client_info(
        Patient.TABLENAME, device, clientpk, era)
    if serverpk is None:
        return Patient()
    return Patient(serverpk)

# We were looking up ID descriptors from the device's stored variables.
# However, that is a bit of a nuisance for a server-side researcher, and
# it's a pain to copy the server's storedvar values (and -- all or some?)
# when a patient gets individually moved off the tablet. Anyway, they're
# important, so a little repetition is not the end of the world. So,
# let's have the tablet store its current ID descriptors in the patient
# record at the point of upload, and then it's available here directly.
# Thus, always complete and contemporaneous.


def get_patient_server_pks_by_idnum(which_idnum, idnum_value,
                                    current_only=True):
    if not which_idnum or which_idnum < 1 or which_idnum > NUMBER_OF_IDNUMS:
        return []
    if idnum_value is None:
        return []
    query = """
        SELECT _pk
        FROM patient
        WHERE idnum{} = ?
    """.format(which_idnum)
    args = [idnum_value]
    if current_only:
        query += " AND _current"
    return pls.db.fetchallfirstvalues(query, *args)


# =============================================================================
# Reports
# =============================================================================

class Patient_Report_Distinct(cc_report.Report):
    """Report to show distinct patients."""

    @classmethod
    def get_report_id(cls):
        return "patient_distinct"

    @classmethod
    def get_report_title(cls):
        return u"Patients, distinct by name, sex, DOB, all ID numbers"

    @classmethod
    def get_param_spec_list(cls):
        return []

    def get_rows_descriptions(self):
        # Not easy to get UTF-8 fields out of a query in the column headings!
        # So don't do SELECT idnum8 AS 'idnum8 (Addenbrooke's number)';
        # change it post hoc like this:
        sql = """
            SELECT DISTINCT
                surname
                , forename
                , dob
                , sex
        """
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            sql += ", idnum{}".format(n)
        sql += """
            FROM
                patient
            WHERE
                _current
            ORDER BY
                surname
                , forename
                , dob
                , sex
        """
        (rows, fieldnames) = pls.db.fetchall_with_fieldnames(sql)
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            fieldnames = [
                f.replace(
                    "idnum" + str(n),
                    u"idnum" + str(n) + " (" + pls.get_id_desc(n) + ")"
                )
                for f in fieldnames
            ]
        return (rows, fieldnames)


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests_patient(p):
    """Unit tests for Patient class."""
    # skip make_tables
    unit_test_ignore("", p.get_xml_root)
    unit_test_ignore("", p.get_literals_for_anonymisation)
    unit_test_ignore("", p.get_dates_for_anonymisation)
    unit_test_ignore("", p.get_bare_ptinfo)
    unit_test_ignore("", p.get_idnum_array)
    unit_test_ignore("", p.get_idshortdesc_array)
    unit_test_ignore("", p.satisfies_upload_id_policy)
    unit_test_ignore("", p.satisfies_finalize_id_policy)
    # implicitly tested: satisfies_id_policy
    unit_test_ignore("", p.dump)
    unit_test_ignore("", p.get_surname)
    unit_test_ignore("", p.get_forename)
    unit_test_ignore("", p.get_surname_forename_upper)
    unit_test_ignore("", p.get_dob_html, True)
    unit_test_ignore("", p.get_dob_html, False)
    unit_test_ignore("", p.get_age)
    unit_test_ignore("", p.get_dob)
    unit_test_ignore("", p.get_age_at, cc_dt.get_now_localtz())
    unit_test_ignore("", p.get_age_at_string, "2000-01-01")
    unit_test_ignore("", p.is_female)
    unit_test_ignore("", p.is_male)
    unit_test_ignore("", p.get_sex)
    unit_test_ignore("", p.get_sex_verbose)
    # get_hl7_pid_segment: skipped as no default RecipientDefinition yet
    for i in range(-1, NUMBER_OF_IDNUMS + 1 + 1):  # deliberate
        unit_test_ignore("", p.get_idnum, i)
        unit_test_ignore("", p.get_id_generic, True, i, "desc", "shortdesc",
                         "serverdesc", "servershortdesc", "idnumtext", True)
        unit_test_ignore("", p.get_id_generic, True, i, "desc", "shortdesc",
                         "serverdesc", "servershortdesc", "idnumtext", False)
        unit_test_ignore("", p.get_id_generic, False, i, "desc", "shortdesc",
                         "serverdesc", "servershortdesc", "idnumtext", True)
        unit_test_ignore("", p.get_id_generic, False, i, "desc", "shortdesc",
                         "serverdesc", "servershortdesc", "idnumtext", False)
        unit_test_ignore("", p.get_idnum_conflict_and_html, i, True, True)
        unit_test_ignore("", p.get_idnum_conflict_and_html, i, True, False)
        unit_test_ignore("", p.get_idnum_conflict_and_html, i, False, True)
        unit_test_ignore("", p.get_idnum_conflict_and_html, i, False, False)
        unit_test_ignore("", p.get_iddesc, i)
        unit_test_ignore("", p.get_idshortdesc, i)
    unit_test_ignore("", p.get_idother_html, True)
    unit_test_ignore("", p.get_idother_html, False)
    unit_test_ignore("", p.get_gp_html, True)
    unit_test_ignore("", p.get_gp_html, False)
    unit_test_ignore("", p.get_address_html, True)
    unit_test_ignore("", p.get_address_html, False)
    unit_test_ignore("", p.get_html_for_page_header)
    unit_test_ignore("", p.get_html_for_task_header, True)
    unit_test_ignore("", p.get_html_for_task_header, False)
    unit_test_ignore("", p.get_html_for_webview_patient_column)
    unit_test_ignore("", p.get_conflict_html_for_id_col)
    unit_test_ignore("", p.get_url_edit_patient)
    unit_test_ignore("", p.get_special_notes)

    # Lastly:
    unit_test_ignore("", p.anonymise)


def unit_tests():
    """Unit tests for cc_patient module."""
    current_pks = pls.db.fetchallfirstvalues(
        "SELECT _pk FROM {} WHERE _current".format(Patient.TABLENAME)
    )
    test_pks = [None, current_pks[0]] if current_pks else [None]
    for pk in test_pks:
        p = Patient(pk)
        unit_tests_patient(p)

    unit_test_ignore("", get_current_version_of_patient_by_client_info,
                     "", 0, ERA_NOW)

    # Patient_Report_Distinct: tested via cc_report
