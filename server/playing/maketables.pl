#!/usr/bin/perl -w

# Prerequisite: e.g.
#   CREATE DATABASE camcops;
# Can use this with temporary environment varibles, e.g.:
#   DB_NAME=camcops DB_USER=root DB_PASSWORD=xxx ./maketables

my $deleting = 0; # DANGER. Making this non-zero will wipe the database!

#==============================================================================
# Standard includes
#==============================================================================

use strict;
use warnings;

use DBI;

#==============================================================================
# Language help
#==============================================================================

sub in_A_not_B
{
    # call as in_A_not_B(\@A, \@B)
    my ($refA, $refB) = @_;
    my %seen;
    @seen{@$refA} = ();
    delete @seen{@$refB};
    return keys %seen;
}

sub in_A_not_B_with_C_paired_to_A
{
    my ($refA, $refB, $refC, $refAtrimmed, $refCtrimmed) = @_;
    my %seen;
    @seen{@$refA} = @$refC;
    delete @seen{@$refB};
    @$refAtrimmed = keys %seen; # written back
    @$refCtrimmed = values %seen; # written back
}

#==============================================================================
# Environment variables
#==============================================================================

sub get_env_var_or_fail
{
    my $var = shift;
    my $val = $ENV{$var};
    unless ($val)
    {
        fail("Environment variable $var not set");
    }
    return $val;
}

sub get_db_vars
{
    my $db_name = get_env_var_or_fail("DB_NAME");
    my $db_user = get_env_var_or_fail("DB_USER");
    my $db_password = get_env_var_or_fail("DB_PASSWORD");
    # The next line assumes the use of MySQL.
    return("DBI:mysql:".$db_name.";mysql_enable_utf8=1", # DSN
           $db_user,
           $db_password);
}

#==============================================================================
# Database globals and error handling
#==============================================================================

sub fail
{
    my $err = shift;
    print("$err\n");
    exit 1;
}

sub dbi_error_handler
{
    my ($message, $handle, $first_value) = @_;
    fail("Database error: $message");
}

# Connect to database
my ($dsn, $dbuser, $dbpassword) = get_db_vars();
my $dbh = DBI->connect($dsn, $dbuser, $dbpassword, {
    #PrintError => 1,  # report errors via warn()?
    #RaiseError => 0 # report errors via die()?
    ShowErrorStatement => 1, # adds the offending SQL to the error message
    HandleError => \&dbi_error_handler # provide a custom function to handle errors
}) || fail("Couldn't connect to database: $DBI::errstr");
print("Connected to database: $dsn\n");

#==============================================================================
# Database manipulation
#==============================================================================

sub create_table
{
    my ($table, @fielddefs) = @_;
    if ($deleting)
    {
        print "Deleting table $table\n";
        $dbh->do("DROP TABLE IF EXISTS $table");
    }
    my $sql = "CREATE TABLE IF NOT EXISTS $table (" . join(',', @fielddefs) . ")" ;
    print "Creating table $table\n";
    #print "$sql\n\n";
    $dbh->do($sql);
}

sub get_field_names_from_db
{
    my ($table) = @_;
    my $sql = "SHOW COLUMNS FROM $table"; # MySQL; returns field/type/null/key/default/extra
    my $sth = $dbh->prepare($sql);
    $sth->execute();
    my @fields_in_db;
    while (my @rowarray = $sth->fetchrow_array())
    {
        push(@fields_in_db, $rowarray[0]);
    }
    return @fields_in_db;
}

sub create_or_update_table_with_final
{
    my ($table, $ref_fielddefs, $ref_final) = @_;
    my @fielddefs = @$ref_fielddefs;
    my @final = @$ref_final;

    # Make the table
    create_table($table, @fielddefs, @final);

    # Now, are the fields all there?
    my @fields_in_db = get_field_names_from_db($table);
    my @fields_in_list;
    foreach my $fd (@fielddefs)
    {
        my ($fieldname) = split(' ', $fd);
        push(@fields_in_list, $fieldname);
    }
    #print "fields_in_db: @fields_in_db\n";
    #print "fields_in_list: @fields_in_list\n";
    my @missing_fields;
    my @missing_fielddefs;
    in_A_not_B_with_C_paired_to_A(\@fields_in_list, \@fields_in_db, \@fielddefs, \@missing_fields, \@missing_fielddefs);
    if (@missing_fields)
    {
        print "... missing fields: @missing_fields\n";
        foreach my $fd (@missing_fielddefs)
        {
            my $sql = "ALTER TABLE $table ADD COLUMN $fd";
            print "$sql\n";
            $dbh->do($sql);
        }
    }

    # Anything superfluous?
    my @superfluous_fields = in_A_not_B(\@fields_in_db, \@fields_in_list);
    if (@superfluous_fields)
    {
        print "... superfluous fields (ignored): @superfluous_fields\n";
    }
}

sub create_or_update_table
{
   my ($table, @fielddefs) = @_;
   my @final;
   create_or_update_table_with_final($table, \@fielddefs, \@final);
}

sub index_exists
{
    my ($table, $indexname) = @_;
    my $sql = "SELECT COUNT(*) FROM information_schema.statistics WHERE table_name=? AND index_name=?";
    my $sth = $dbh->prepare($sql);
    $sth->execute($table, $indexname);
    my $count = $sth->fetchrow_array(); # only one row, only one column
    return ($count > 0);
}

sub create_index
{
    my ($table, $field, $nchars) = @_;
    my $limit = "";
    if (defined($nchars))
    {
        $limit = "($nchars)";
    }
    my $indexname = "_idx$field";
    if (index_exists($table, $indexname))
    {
        return;
    }
    my $sql = "CREATE INDEX $indexname ON $table ($field$limit)";
    $dbh->do($sql);
}

sub create_current_view
{
    my ($table) = @_;
    my $sql = "CREATE OR REPLACE VIEW ${table}_current AS SELECT * FROM $table WHERE _current";
    $dbh->do($sql);
}

sub create_standard_table
{
    my ($table, @client_fielddefs) = @_;
    # Arrays are flattened to a list. (The alternative method is to pass an array reference.)
    # Define fields that the server adds to all tables
    my @standard_server_fielddefs = (
        "_pk INTEGER NOT NULL AUTO_INCREMENT", # PK; MySQL syntax
        "_device TEXT NOT NULL",
        "_current BOOLEAN NOT NULL",
        "_deleted BOOLEAN NOT NULL",
        "_modified BOOLEAN NOT NULL",
        "_date_added TEXT",
        "_date_removed TEXT",
        "_adding_user TEXT",
        "_removing_user TEXT",
        "_date_frozen TEXT",
        "_freezing_mark TEXT",
        "_freezing_user TEXT"
    );
    # Define fields that *all* client tables have
    my @standard_client_fielddefs = ("modification_date TEXT");
    my @final = ("PRIMARY KEY(_pk)"); # MySQL syntax
    my @fielddefs = (@standard_server_fielddefs, @client_fielddefs, @standard_client_fielddefs);

    create_or_update_table_with_final($table, \@fielddefs, \@final);
    create_index($table, "_device", 50);
    create_index($table, "_current");
    create_current_view($table);
}

sub create_standard_task_table
{
    # Define fields that nearly all tasks have
    my ($table, @task_specific_fielddefs) = @_;
    my @fielddefs = (
        "id INTEGER NOT NULL", # PK on the client side
        "patient_id INTEGER NOT NULL",
        "datetime TEXT NOT NULL",
        "firstexit_is_finish BOOLEAN",
        "firstexit_is_abort BOOLEAN",
        "firstexit_datetime TEXT",
    );
    push(@fielddefs, @task_specific_fielddefs); # appends the second to the first
    create_standard_table($table, @fielddefs); 
    create_index($table, "id");
    create_index($table, "patient_id");
}

sub create_standard_ancillary_table
{
   my ($table, @task_specific_fielddefs) = @_;
    my @fielddefs = (
        "id INTEGER NOT NULL", # PK on the client side
        # The rest is up to the task...
    );
    push(@fielddefs, @task_specific_fielddefs); # appends the second to the first
    create_standard_table($table, @fielddefs); 
}

sub repeat_fielddef
{
   my ($prefix, $start, $end, $type) = @_;
   my @fielddefs;
   foreach my $i ($start..$end)
   {
       my $field = "$prefix$i $type";
       push(@fielddefs, $field);
   }
   return @fielddefs;
}

#==============================================================================
# Main
#==============================================================================

#------------------------------------------------------------------------------
# Internal tables
#------------------------------------------------------------------------------

if ($deleting)
{
    $dbh->do("DROP TABLE IF EXISTS _security_users");
    $dbh->do("DROP TABLE IF EXISTS _security_devices");
}

create_or_update_table("_security_users",
    "user VARCHAR(255) PRIMARY KEY",
    "salt VARCHAR(255) NOT NULL",
    "hash VARCHAR(255) NOT NULL",
    "last_password_change DATETIME",
    "may_register_devices BOOLEAN",
    "may_use_webstorage BOOLEAN",
    "may_use_webviewer BOOLEAN",
    "may_view_other_users_records BOOLEAN",
    "may_alter_users BOOLEAN",
);

create_or_update_table("_security_devices",
    "device VARCHAR(255) PRIMARY KEY",
    "registered_by_user VARCHAR(255)",
    "registered_when TEXT",
    "friendly_name TEXT"
);

create_or_update_table("_security_webviewer_sessions",
    "id VARCHAR(50) PRIMARY KEY",
    "user VARCHAR(255)",
    "ip_address VARCHAR(40)",
    "last_activity DATETIME",
    "filter_surname TEXT",
    "filter_forename TEXT",
    "filter_sex TEXT",
    "filter_idnum1 INTEGER",
    "filter_idnum2 INTEGER",
    "filter_idnum3 INTEGER",
    "filter_idnum4 INTEGER",
    "filter_task TEXT",
    "filter_complete BOOLEAN",
    "filter_device TEXT",
    "number_to_view INTEGER",
    "first_task_to_view INTEGER"
);

create_or_update_table("_freezing_temp",
    "id INTEGER PRIMARY KEY AUTO_INCREMENT",
    "device VARCHAR(255)",
    "freeze_at TEXT",
    "tablename TEXT"
);

#------------------------------------------------------------------------------
# Core tables
#------------------------------------------------------------------------------

create_standard_table("patient",
    "id INTEGER NOT NULL", # PK on the client side
    "forename TEXT NOT NULL",
    "surname TEXT NOT NULL",
    "dob TEXT NOT NULL",
    "sex VARCHAR(1) NOT NULL",
    "idnum1 INTEGER",
    "idnum2 INTEGER",
    "idnum3 INTEGER",
    "idnum4 INTEGER",
    "address TEXT",
    "gp TEXT",
    "other TEXT"
);

create_standard_table("storedvars",
    "id INTEGER NOT NULL", # notional PK on the client side
    "name VARCHAR(255) NOT NULL", # effective PK on the client side
    "type VARCHAR(255) NOT NULL",
    "valueInteger INTEGER",
    "valueText TEXT",
    "valueReal REAL"
);

create_standard_table("blobs",
    "id INTEGER NOT NULL", # PK on the client side
    "tablename TEXT NOT NULL",
    "tablepk INTEGER NOT NULL",
    "fieldname TEXT NOT NULL",
    "filename TEXT",
    "theblob LONGBLOB"
);

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Task tables
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#------------------------------------------------------------------------------
# Clinical
#------------------------------------------------------------------------------

create_standard_task_table("clinicalphoto",
    "description TEXT",
    "photo_blobid INTEGER"
);
create_standard_task_table("clinicalshortnote",
    "clinician_specialty TEXT",
    "clinician_name TEXT",
    "clinician_post TEXT",
    "clinician_contact_details TEXT",
    "location TEXT",
    "note TEXT",
);
create_standard_task_table("clinicalcontactlog",
    "clinician_name TEXT",
    "location TEXT",
    "start TEXT",
    "end TEXT",
    "patient_contact INTEGER",
    "staff_liaison INTEGER",
    "other_liaison INTEGER",
    "comment TEXT"
);
create_standard_task_table("clinicalclerking",
    "clinician_specialty TEXT",
    "clinician_name TEXT",
    "clinician_post TEXT",
    "clinician_contact_details TEXT",
    "location TEXT",
    "preamble TEXT",
    "reason_for_assessment TEXT",
    "history_of_presenting_complaint TEXT",
    "systems_review TEXT",
    "collateral_history TEXT",
    "past_psychiatric_history TEXT",
    "past_medical_history TEXT",
    "allergies_and_intolerances TEXT",
    "medications TEXT",
    "recreational_drug_use TEXT",
    "family_history TEXT",
    "developmental_history TEXT",
    "personal_history TEXT",
    "premorbid_personality TEXT",
    "forensic_history TEXT",
    "current_social_situation TEXT",
    "mse_appearance_behaviour TEXT",
    "mse_speech TEXT",
    "mse_mood_subjective TEXT",
    "mse_mood_objective TEXT",
    "mse_thought_form TEXT",
    "mse_thought_content TEXT",
    "mse_perception TEXT",
    "mse_cognition TEXT",
    "mse_insight TEXT",
    "risk TEXT",
    "physical_examination_general TEXT",
    "physical_examination_cardiovascular TEXT",
    "physical_examination_respiratory TEXT",
    "physical_examination_abdominal TEXT",
    "physical_examination_neurological TEXT",
    "investigations TEXT",
    "summary TEXT",
    "impression TEXT",
    "plan TEXT"
);

#------------------------------------------------------------------------------
# Global
#------------------------------------------------------------------------------

create_standard_task_table("bprs", repeat_fielddef("q", 1, 20, "INTEGER"));
create_standard_task_table("bprse", repeat_fielddef("q", 1, 24, "INTEGER"));
create_standard_task_table("cgi",
    "q1 INTEGER", "q2 INTEGER", "q3t INTEGER", "q3s INTEGER", "q3 INTEGER" # non-standard names
);
create_standard_task_table("distressthermometer",
    "distress INTEGER",
    repeat_fielddef("q", 1, 36, "INTEGER"),
    "other TEXT"
);
create_standard_task_table("honos",
    "period_rated TEXT",
    repeat_fielddef("q", 1, 12, "INTEGER"),
    "q8problemtype VARCHAR(1)",
    "q8otherproblem TEXT"
);
create_standard_task_table("honos65",
    "period_rated TEXT",
    repeat_fielddef("q", 1, 12, "INTEGER"),
    "q8problemtype VARCHAR(1)",
    "q8otherproblem TEXT"
);
create_standard_task_table("honosca",
    "period_rated TEXT",
    repeat_fielddef("q", 1, 15, "INTEGER")
);

#------------------------------------------------------------------------------
# Cognitive
#------------------------------------------------------------------------------

create_standard_task_table("ace3",
    "tester_name TEXT",
    "age_at_leaving_full_time_education INTEGER",
    "occupation TEXT",
    "handedness TEXT",
    repeat_fielddef("attn_time", 1, 5, "INTEGER"),
    repeat_fielddef("attn_place", 1, 5, "INTEGER"),
    repeat_fielddef("attn_repeat_word", 1, 3, "INTEGER"),
    "attn_num_registration_trials INTEGER",
    repeat_fielddef("attn_serial7_subtraction", 1, 5, "INTEGER"),
    repeat_fielddef("mem_recall_word", 1, 3, "INTEGER"),
    # "fluency_letters_correct INTEGER",
    # "fluency_letters_incorrect INTEGER",
    # "fluency_animals_correct INTEGER",
    # "fluency_animals_incorrect INTEGER",
    "fluency_letters_score INTEGER",
    "fluency_animals_score INTEGER",
    repeat_fielddef("mem_repeat_address_trial1_", 1, 7, "INTEGER"),
    repeat_fielddef("mem_repeat_address_trial2_", 1, 7, "INTEGER"),
    repeat_fielddef("mem_repeat_address_trial3_", 1, 7, "INTEGER"),
    repeat_fielddef("mem_famous", 1, 4, "INTEGER"),
    "lang_follow_command_practice INTEGER",
    repeat_fielddef("lang_follow_command", 1, 3, "INTEGER"),
    repeat_fielddef("lang_write_sentences_point", 1, 2, "INTEGER"),
    repeat_fielddef("lang_repeat_word", 1, 4, "INTEGER"),
    repeat_fielddef("lang_repeat_sentence", 1, 2, "INTEGER"),
    repeat_fielddef("lang_name_picture", 1, 12, "INTEGER"),
    repeat_fielddef("lang_identify_concept", 1, 4, "INTEGER"),
    "lang_read_words_aloud INTEGER",
    "vsp_copy_infinity INTEGER",
    "vsp_copy_cube INTEGER",
    "vsp_draw_clock INTEGER",
    repeat_fielddef("vsp_count_dots", 1, 4, "INTEGER"),
    repeat_fielddef("vsp_identify_letter", 1, 4, "INTEGER"),
    repeat_fielddef("mem_recall_address", 1, 7, "INTEGER"),
    repeat_fielddef("mem_recognize_address", 1, 5, "INTEGER"),
    "picture1_blobid INTEGER",
    "picture2_blobid INTEGER"
);

create_standard_task_table("moca",
    repeat_fielddef("q", 1, 28, "INTEGER"),
    "education12y_or_less INTEGER",
    "trailpicture_blobid INTEGER",
    "cubepicture_blobid INTEGER",
    "clockpicture_blobid INTEGER",
    repeat_fielddef("register_trial1_", 1, 5, "INTEGER"),
    repeat_fielddef("register_trial2_", 1, 5, "INTEGER"),
    repeat_fielddef("recall_category_cue_", 1, 5, "INTEGER"),
    repeat_fielddef("recall_mc_cue_", 1, 5, "INTEGER")
);

create_standard_task_table("slums",
    "alert INTEGER",
    "highschooleducation INTEGER",
    "q1 INTEGER", "q2 INTEGER", "q3 INTEGER", "q5a INTEGER", "q5b INTEGER", # non-standard names
    "q6 INTEGER", "q7a INTEGER", "q7b INTEGER", "q7c INTEGER", "q7d INTEGER", "q7e INTEGER",
    "q8b INTEGER", "q8c INTEGER", "q9a INTEGER", "q9b INTEGER", "q10a INTEGER", "q10b INTEGER",
    "q11a INTEGER", "q11b INTEGER", "q11c INTEGER", "q11d INTEGER", "q11e INTEGER",
    "clockpicture_blobid INTEGER", "shapespicture_blobid INTEGER"
);

#------------------------------------------------------------------------------
# Affective
#------------------------------------------------------------------------------

create_standard_task_table("asrm", repeat_fielddef("q", 1, 5, "INTEGER"));
create_standard_task_table("epds", repeat_fielddef("q", 1, 10, "INTEGER"));
create_standard_task_table("gad7", repeat_fielddef("q", 1, 7, "INTEGER"));
create_standard_task_table("hama", repeat_fielddef("q", 1, 14, "INTEGER"));
create_standard_task_table("hamd",
    repeat_fielddef("q", 1, 15, "INTEGER"),
    "whichq16 INTEGER",
    "q16a INTEGER",
    "q16b INTEGER",
    "q17 INTEGER",
    "q18a INTEGER",
    "q18b INTEGER",
    repeat_fielddef("q", 19, 21, "INTEGER")
);
create_standard_task_table("hamd7", repeat_fielddef("q", 1, 7, "INTEGER"));
create_standard_task_table("madrs",
    repeat_fielddef("q", 1, 10, "INTEGER"),
    "period_rated TEXT"
);
create_standard_task_table("pclc", repeat_fielddef("q", 1, 17, "INTEGER"));
create_standard_task_table("pclm", repeat_fielddef("q", 1, 17, "INTEGER"));
create_standard_task_table("pcls", repeat_fielddef("q", 1, 17, "INTEGER"), "event TEXT", "eventdate TEXT");
create_standard_task_table("phq9", repeat_fielddef("q", 1, 10, "INTEGER"));
create_standard_task_table("phq15", repeat_fielddef("q", 1, 15, "INTEGER"));

#------------------------------------------------------------------------------
# Drug/alcohol
#------------------------------------------------------------------------------

create_standard_task_table("audit", repeat_fielddef("q", 1, 10, "INTEGER"));
create_standard_task_table("cage", repeat_fielddef("q", 1, 4, "VARCHAR(1)"));
create_standard_task_table("ciwa",
    repeat_fielddef("q", 1, 10, "INTEGER"),
    "t INTEGER",
    "hr INTEGER",
    "sbp INTEGER",
    "dbp INTEGER",
    "rr INTEGER"
);
create_standard_task_table("dast", repeat_fielddef("q", 1, 28, "VARCHAR(1)"));
create_standard_task_table("fast", repeat_fielddef("q", 1, 4, "INTEGER"));
create_standard_task_table("mast", repeat_fielddef("q", 1, 24, "VARCHAR(1)"));
create_standard_task_table("smast", repeat_fielddef("q", 1, 13, "VARCHAR(1)"));

#------------------------------------------------------------------------------
# Psychosis
#------------------------------------------------------------------------------

create_standard_task_table("lshs_a", repeat_fielddef("q", 1, 12, "INTEGER"));
create_standard_task_table("lshs_laroi2005", repeat_fielddef("q", 1, 16, "INTEGER"));
create_standard_task_table("panss",
    repeat_fielddef("p", 1, 7, "INTEGER"),
    repeat_fielddef("n", 1, 7, "INTEGER"),
    repeat_fielddef("g", 1, 16, "INTEGER")
);

#------------------------------------------------------------------------------
# Catatonia/EPSE
#------------------------------------------------------------------------------

create_standard_task_table("aims", repeat_fielddef("q", 1, 12, "INTEGER"));
create_standard_task_table("bars", repeat_fielddef("q", 1, 4, "INTEGER"));

#------------------------------------------------------------------------------
# Executive
#------------------------------------------------------------------------------

create_standard_task_table("fab", repeat_fielddef("q", 1, 6, "INTEGER"));

#------------------------------------------------------------------------------
# Demo
#------------------------------------------------------------------------------

create_standard_task_table("demoquestionnaire",
    repeat_fielddef("mcq", 1, 8, "INTEGER"),
    repeat_fielddef("mcqbool", 1, 3, "INTEGER"),
    repeat_fielddef("multipleresponse", 1, 6, "INTEGER"),
    repeat_fielddef("booltext", 1, 21, "INTEGER"),
    repeat_fielddef("slider", 1, 2, "REAL"),
    "boolimage INTEGER",
    "typedvar_text TEXT",
    "typedvar_text_multiline TEXT",
    "typedvar_int INTEGER",
    "typedvar_real REAL",
    "date_only TEXT",
    "date_time TEXT",
    "thermometer INTEGER",
    "photo_blobid INTEGER",
    "canvas_blobid INTEGER"
);

#------------------------------------------------------------------------------
# Research
#------------------------------------------------------------------------------

# Quality of life

create_standard_task_table("qolbasic",
    "tto REAL",
    "rs REAL"
);

create_standard_task_table("qolsg",
    "category_start_time TEXT",
    "category_responded INTEGER",
    "category_response_time TEXT",
    "category_chosen TEXT",
    "gamble_fixed_option TEXT",
    "gamble_lottery_option_p TEXT",
    "gamble_lottery_option_q TEXT",
    "gamble_lottery_on_left INTEGER",
    "gamble_starting_p REAL",
    "gamble_start_time TEXT",
    "gamble_responded INTEGER",
    "gamble_response_time TEXT",
    "gamble_p REAL",
    "utility REAL"
);

# ExpDetThreshold

create_standard_task_table("expdetthreshold",
    # Config
    "modality INTEGER",
    "target_number INTEGER",
    "background_filename TEXT",
    "target_filename TEXT",
    "visual_target_duration_s REAL",
    "background_intensity REAL",
    "start_intensity_min REAL",
    "start_intensity_max REAL",
    "initial_large_intensity_step REAL",
    "main_small_intensity_step REAL",
    "num_trials_in_main_sequence INTEGER",
    "p_catch_trial REAL",
    "prompt TEXT",
    "iti_s REAL",
    # Results
    "finished INTEGER",
    "intercept REAL",
    "slope REAL",
    "k REAL",
    "theta REAL",
    "x20 REAL",
    "x50 REAL",
    "x80 REAL"
);
create_standard_ancillary_table("expddetthreshold_trials",
    # Keys, other than the PK
    "expdetthreshold_id INTEGER NOT NULL",
    "trial INTEGER NOT NULL",
    # Results
    "trial_ignoring_catch_trials INTEGER",
    "target_presented INTEGER",
    "target_time TEXT",
    "intensity REAL",
    "choice_time TEXT",
    "responded INTEGER",
    "response_time TEXT",
    "response_latency_ms INTEGER",
    "yes INTEGER",
    "no INTEGER",
    "caught_out_reset INTEGER",
    "trial_num_in_calculation_sequence INTEGER"
);

# Expectation-detection task

create_standard_task_table("expectationdetection",
    # Config
    "num_blocks INTEGER",
    "stimulus_counterbalancing INTEGER",
    "is_detection_response_on_right INTEGER",
    "pause_every_n_trials INTEGER",
    # ... cue
    "cue_duration_s REAL",
    "visual_cue_intensity REAL",
    "auditory_cue_intensity REAL",
    # ... ISI
    "isi_duration_s REAL",
    # .. target
    "visual_target_duration_s REAL",
    "visual_background_intensity REAL",
    "visual_target_0_intensity REAL",
    "visual_target_1_intensity REAL",
    "auditory_background_intensity REAL",
    "auditory_target_0_intensity REAL",
    "auditory_target_1_intensity REAL",
    # ... ITI
    "iti_min_s REAL",
    "iti_max_s REAL",
    # Results
    "finished INTEGER",
    "last_trial_completed INTEGER"
);
create_standard_ancillary_table("expectationdetection_trialgroupspec",
    "expectationdetection_id INTEGER NOT NULL",
    "group_num INTEGER NOT NULL",
    # Group spec
    "cue INTEGER",
    "target_modality INTEGER",
    "target_number INTEGER",
    "n_target INTEGER",
    "n_no_target INTEGER",
);
create_standard_ancillary_table("expectationdetection_trials",
    "expectationdetection_id INTEGER NOT NULL",
    "trial INTEGER NOT NULL",
    # Config determines these (via an autogeneration process):
    "block INTEGER",
    "group_num INTEGER",
    "cue INTEGER",
    "raw_cue_number INTEGER",
    "target_modality INTEGER",
    "target_number INTEGER",
    "target_present INTEGER",
    "iti_length_s REAL",
    # Task determines these (on the fly):
    "pause_given_before_trial INTEGER",
    "pause_start_time TEXT",
    "pause_end_time TEXT",
    "trial_start_time TEXT",
    "cue_start_time TEXT",
    "target_start_time TEXT",
    "detection_start_time TEXT",
    "iti_start_time TEXT",
    "iti_end_time TEXT",
    "trial_end_time TEXT",
    # Subject decides these:
    "responded INTEGER",
    "response_time TEXT",
    "response_latency_ms INTEGER",
    "rating INTEGER"
);                           

#------------------------------------------------------------------------------
# Anonymous
#------------------------------------------------------------------------------

create_standard_task_table("gmcpq",
    "doctor TEXT",
    "q1 INTEGER",
    "q2a INTEGER",
    "q2b INTEGER",
    "q2c INTEGER",
    "q2d INTEGER",
    "q2e INTEGER",
    "q2f INTEGER",
    "q2f_details TEXT",
    "q3 INTEGER",
    "q4a INTEGER",
    "q4b INTEGER",
    "q4c INTEGER",
    "q4d INTEGER",
    "q4e INTEGER",
    "q4f INTEGER",
    "q4g INTEGER",
    "q5a INTEGER",
    "q5b INTEGER",
    "q6 INTEGER",
    "q7 INTEGER",
    "q8 INTEGER",
    "q9 TEXT",
    "q10 TEXT", # sex
    "q11 INTEGER",
    "q12 INTEGER",
    "q12_details TEXT"
);

#------------------------------------------------------------------------------
# Permission refused
#------------------------------------------------------------------------------

my $PERMISSION_REFUSED = '
    create_standard_task_table("bfcrs", repeat_fielddef("q", 1, 23, "INTEGER"));
    create_standard_task_table("csi", repeat_fielddef("q", 1, 14, "INTEGER"));
    create_standard_task_table("sas", repeat_fielddef("q", 1, 10, "INTEGER"));
    create_standard_task_table("lunsers", repeat_fielddef("q", 1, 51, "INTEGER"));
    create_standard_task_table("gass",
        "medication TEXT",
        repeat_fielddef("q", 1, 22, "INTEGER"),
        repeat_fielddef("d", 1, 22, "INTEGER"),
    );
';

#==============================================================================
# End
#==============================================================================

print "Finished.\n";
exit 0;
