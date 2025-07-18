"""
camcops_server/alembic/versions/0014_new_export_mechanism.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

DATABASE REVISION SCRIPT

New export mechanism

Revision ID: 0014
Revises: 0013
Creation date: 2018-12-17 22:58:47.428288

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import cardinal_pythonlib.sqlalchemy.list_types


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================


# noinspection PyPep8,PyTypeChecker
def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "_emails",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at_utc", sa.DateTime(), nullable=True),
        sa.Column("date", sa.String(length=31), nullable=True),
        sa.Column("from_addr", sa.Unicode(length=255), nullable=True),
        sa.Column("sender", sa.Unicode(length=255), nullable=True),
        sa.Column("reply_to", sa.Unicode(length=255), nullable=True),
        sa.Column("to", sa.Text(), nullable=True),
        sa.Column("cc", sa.Text(), nullable=True),
        sa.Column("bcc", sa.Text(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("charset", sa.String(length=64), nullable=True),
        sa.Column(
            "msg_string",
            sa.UnicodeText().with_variant(mysql.LONGTEXT, "mysql"),
            nullable=True,
        ),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("use_tls", sa.Boolean(), nullable=True),
        sa.Column("sent", sa.Boolean(), nullable=False),
        sa.Column("sent_at_utc", sa.DateTime(), nullable=True),
        sa.Column("sending_failure_reason", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__emails")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )

    op.create_table(
        "_export_recipients",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("recipient_name", sa.String(length=191), nullable=False),
        sa.Column("current", sa.Boolean(), nullable=False),
        sa.Column("transmission_method", sa.String(length=50), nullable=False),
        sa.Column("push", sa.Boolean(), nullable=False),
        sa.Column("task_format", sa.String(length=50), nullable=True),
        sa.Column("xml_field_comments", sa.Boolean(), nullable=False),
        sa.Column("all_groups", sa.Boolean(), nullable=False),
        sa.Column(
            "group_ids",
            cardinal_pythonlib.sqlalchemy.list_types.IntListType(),
            nullable=True,
        ),
        sa.Column("start_datetime_utc", sa.DateTime(), nullable=True),
        sa.Column("end_datetime_utc", sa.DateTime(), nullable=True),
        sa.Column("finalized_only", sa.Boolean(), nullable=False),
        sa.Column("include_anonymous", sa.Boolean(), nullable=False),
        sa.Column("primary_idnum", sa.Integer(), nullable=False),
        sa.Column("require_idnum_mandatory", sa.Boolean(), nullable=True),
        sa.Column("db_url", sa.String(length=255), nullable=True),
        sa.Column("db_echo", sa.Boolean(), nullable=False),
        sa.Column("db_include_blobs", sa.Boolean(), nullable=False),
        sa.Column("db_add_summaries", sa.Boolean(), nullable=False),
        sa.Column("db_patient_id_per_row", sa.Boolean(), nullable=False),
        sa.Column("email_host", sa.String(length=255), nullable=True),
        sa.Column("email_port", sa.Integer(), nullable=True),
        sa.Column("email_use_tls", sa.Boolean(), nullable=False),
        sa.Column("email_host_username", sa.String(length=255), nullable=True),
        sa.Column("email_from", sa.Unicode(length=255), nullable=True),
        sa.Column("email_sender", sa.Unicode(length=255), nullable=True),
        sa.Column("email_reply_to", sa.Unicode(length=255), nullable=True),
        sa.Column("email_to", sa.Text(), nullable=True),
        sa.Column("email_cc", sa.Text(), nullable=True),
        sa.Column("email_bcc", sa.Text(), nullable=True),
        sa.Column("email_patient", sa.Unicode(length=255), nullable=True),
        sa.Column(
            "email_patient_spec_if_anonymous",
            sa.Unicode(length=255),
            nullable=True,
        ),
        sa.Column("email_subject", sa.Unicode(length=255), nullable=True),
        sa.Column("email_body_as_html", sa.Boolean(), nullable=False),
        sa.Column("email_body", sa.Text(), nullable=True),
        sa.Column("email_keep_message", sa.Boolean(), nullable=False),
        sa.Column("hl7_host", sa.String(length=255), nullable=True),
        sa.Column("hl7_port", sa.Integer(), nullable=True),
        sa.Column("hl7_ping_first", sa.Boolean(), nullable=False),
        sa.Column("hl7_network_timeout_ms", sa.Integer(), nullable=True),
        sa.Column("hl7_keep_message", sa.Boolean(), nullable=False),
        sa.Column("hl7_keep_reply", sa.Boolean(), nullable=False),
        sa.Column("hl7_debug_divert_to_file", sa.Boolean(), nullable=False),
        sa.Column(
            "hl7_debug_treat_diverted_as_sent", sa.Boolean(), nullable=False
        ),
        sa.Column("file_patient_spec", sa.Unicode(length=255), nullable=True),
        sa.Column(
            "file_patient_spec_if_anonymous",
            sa.Unicode(length=255),
            nullable=True,
        ),
        sa.Column("file_filename_spec", sa.Unicode(length=255), nullable=True),
        sa.Column("file_make_directory", sa.Boolean(), nullable=False),
        sa.Column("file_overwrite_files", sa.Boolean(), nullable=False),
        sa.Column("file_export_rio_metadata", sa.Boolean(), nullable=False),
        sa.Column("file_script_after_export", sa.Text(), nullable=True),
        sa.Column("rio_idnum", sa.Integer(), nullable=True),
        sa.Column("rio_uploading_user", sa.Text(), nullable=True),
        sa.Column("rio_document_type", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__export_recipients")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("_export_recipients", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix__export_recipients_id"), ["id"], unique=False
        )

    op.create_table(
        "_exported_tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("recipient_id", sa.BigInteger(), nullable=False),
        sa.Column("basetable", sa.String(length=128), nullable=False),
        sa.Column("task_server_pk", sa.Integer(), nullable=False),
        sa.Column("start_at_utc", sa.DateTime(), nullable=False),
        sa.Column("finish_at_utc", sa.DateTime(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column(
            "failure_reasons",
            cardinal_pythonlib.sqlalchemy.list_types.StringListType(),
            nullable=True,
        ),
        sa.Column("cancelled", sa.Boolean(), nullable=False),
        sa.Column("cancelled_at_utc", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["_export_recipients.id"],
            name=op.f("fk__exported_tasks_recipient_id"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__exported_tasks")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("_exported_tasks", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix__exported_tasks_basetable"),
            ["basetable"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix__exported_tasks_task_server_pk"),
            ["task_server_pk"],
            unique=False,
        )

    op.create_table(
        "_exported_task_email",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("exported_task_id", sa.BigInteger(), nullable=False),
        sa.Column("email_id", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["email_id"],
            ["_emails.id"],
            name=op.f("fk__exported_task_email_email_id"),
        ),
        sa.ForeignKeyConstraint(
            ["exported_task_id"],
            ["_exported_tasks.id"],
            name=op.f("fk__exported_task_email_exported_task_id"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__exported_task_email")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )

    op.create_table(
        "_exported_task_filegroup",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("exported_task_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "filenames",
            cardinal_pythonlib.sqlalchemy.list_types.StringListType(),
            nullable=True,
        ),
        sa.Column("script_called", sa.Boolean(), nullable=False),
        sa.Column("script_retcode", sa.Integer(), nullable=True),
        sa.Column("script_stdout", sa.UnicodeText(), nullable=True),
        sa.Column("script_stderr", sa.UnicodeText(), nullable=True),
        sa.ForeignKeyConstraint(
            ["exported_task_id"],
            ["_exported_tasks.id"],
            name=op.f("fk__exported_task_filegroup_exported_task_id"),
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("pk__exported_task_filegroup")
        ),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )

    op.create_table(
        "_exported_task_hl7msg",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("exported_task_id", sa.BigInteger(), nullable=False),
        sa.Column("sent_at_utc", sa.DateTime(), nullable=True),
        sa.Column("reply_at_utc", sa.DateTime(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column(
            "message",
            sa.UnicodeText().with_variant(mysql.LONGTEXT, "mysql"),
            nullable=True,
        ),
        sa.Column("reply", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["exported_task_id"],
            ["_exported_tasks.id"],
            name=op.f("fk__exported_task_hl7msg_exported_task_id"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__exported_task_hl7msg")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )

    op.drop_table("_hl7_message_log")

    op.drop_table("_hl7_run_log")

    with op.batch_alter_table("_idnum_index", schema=None) as batch_op:
        batch_op.create_foreign_key(
            batch_op.f("fk__idnum_index_patient_pk"),
            "patient",
            ["patient_pk"],
            ["_pk"],
        )

    with op.batch_alter_table("_task_index", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix__task_index_when_added_batch_utc"),
            ["when_added_batch_utc"],
            unique=False,
        )

    # ### end Alembic commands ###


# noinspection PyPep8,PyTypeChecker
def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("_task_index", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix__task_index_when_added_batch_utc"))

    with op.batch_alter_table("_idnum_index", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk__idnum_index_patient_pk"), type_="foreignkey"
        )

    op.create_table(
        "_hl7_run_log",
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("start_at_utc", sa.DateTime(), nullable=False),
        sa.Column("finish_at_utc", sa.DateTime(), nullable=True),
        sa.Column("recipient", sa.String(length=255), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("primary_idnum", sa.Integer(), nullable=False),
        sa.Column("require_idnum_mandatory", sa.Boolean(), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("finalized_only", sa.Boolean(), nullable=True),
        sa.Column("task_format", sa.String(length=50), nullable=True),
        sa.Column("xml_field_comments", sa.Boolean(), nullable=True),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("divert_to_file", sa.Text(), nullable=True),
        sa.Column("treat_diverted_as_sent", sa.Boolean(), nullable=True),
        sa.Column("include_anonymous", sa.Boolean(), nullable=True),
        sa.Column("overwrite_files", sa.Boolean(), nullable=True),
        sa.Column("rio_metadata", sa.Boolean(), nullable=True),
        sa.Column("rio_idnum", sa.Integer(), nullable=True),
        sa.Column("rio_uploading_user", sa.Text(), nullable=True),
        sa.Column("rio_document_type", sa.Text(), nullable=True),
        sa.Column("script_after_file_export", sa.Text(), nullable=True),
        sa.Column("script_retcode", sa.Integer(), nullable=True),
        sa.Column("script_stdout", sa.UnicodeText(), nullable=True),
        sa.Column("script_stderr", sa.UnicodeText(), nullable=True),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["_security_groups.id"],
            name=op.f("fk__hl7_run_log_group_id"),
        ),
        sa.PrimaryKeyConstraint("run_id", name=op.f("pk__hl7_run_log")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("_hl7_run_log", schema=None) as batch_op:
        batch_op.create_index(
            "ix__hl7_run_log_start_at_utc", ["start_at_utc"], unique=False
        )
        batch_op.create_index(
            "ix__hl7_run_log_recipient", ["recipient"], unique=False
        )
        batch_op.create_index(
            "ix__hl7_run_log_group_id", ["group_id"], unique=False
        )

    op.create_table(
        "_hl7_message_log",
        sa.Column("msg_id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=True),
        sa.Column("basetable", sa.String(length=128), nullable=True),
        sa.Column("serverpk", sa.Integer(), nullable=True),
        sa.Column("sent_at_utc", sa.DateTime(), nullable=True),
        sa.Column("reply_at_utc", sa.DateTime(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column(
            "message",
            sa.UnicodeText().with_variant(mysql.LONGTEXT, "mysql"),
            nullable=True,
        ),
        sa.Column("reply", sa.Text(), nullable=True),
        sa.Column("filename", sa.Text(), nullable=True),
        sa.Column("rio_metadata_filename", sa.Text(), nullable=True),
        sa.Column("cancelled", sa.Boolean(), nullable=True),
        sa.Column("cancelled_at_utc", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["_hl7_run_log.run_id"],
            name="fk__hl7_message_log_run_id",
        ),
        sa.PrimaryKeyConstraint("msg_id", name=op.f("pk__hl7_message_log")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("_hl7_message_log", schema=None) as batch_op:
        batch_op.create_index(
            "ix__hl7_message_log_serverpk", ["serverpk"], unique=False
        )
        batch_op.create_index(
            "ix__hl7_message_log_basetable", ["basetable"], unique=False
        )

    op.drop_table("_exported_task_hl7msg")
    op.drop_table("_exported_task_filegroup")
    op.drop_table("_exported_task_email")
    op.drop_table("_exported_tasks")
    op.drop_table("_export_recipients")
    op.drop_table("_emails")
    # ### end Alembic commands ###
