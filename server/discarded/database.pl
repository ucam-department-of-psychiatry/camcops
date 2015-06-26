#!/usr/bin/perl -w

=pod
    Copyright (C) 2012, 2013 Rudolf Cardinal (rudolf@pobox.com).
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
=cut

#==============================================================================
# INSTALLATION
#==============================================================================
# See http://www.camcops.org/documentation/

#==============================================================================
# Notes
#==============================================================================
# Note that the Perl upload script should NOT attempt to verify patients
# against the ID policy, not least because tablets are allowed to upload
# task data (in a separate transaction) before uploading patients;
# referential integrity would be very hard to police. So the tablet software
# deals with ID compliance. (Also, the user can change the server's ID policy
# retrospectively!)

# *** for mobileweb performance: consider a $commit_immediately option for the
# insert/update functions

#==============================================================================
# Other Perl things to remember
#==============================================================================
# $#array is the index of the last element (-1 if empty)
# scalar(@array) is the number of elements
# BLOBs in Perl/DBI: http://www.james.rcpt.to/programs/mysql/blob/
# http://stackoverflow.com/questions/6740091
# Perl regex examples: http://www.somacon.com/p127.php
# Hashes:
#     Creation: my %hash;
#     Writing scalars: $hash{'key'} = 'value';
#                      $hash($key) = $value;
#                      $hash(key => 'value');
#                      # the fat comma autoquotes the key
#     Reading scalars: my $value = $hash{$key};
#     Reading/writing arrays (multiple keys): see sub in_A_not_B for example
# Referencing: \x makes a reference, e.g. my %hash; my $hashref = \%hash;
# Dereferencing (http://www.perlmeme.org/howtos/using_perl/dereferencing.html):
# ... prefixing a sigil e.g.
#         my $scalar = $$scalarref;
#         my @array = @$arrayref;
#         my $hash = %$hashref;
#         my $sub = &$subref;
# ... thus
#         $$arrayref[0];
#         $$hashref{$key};
#         &$subref();
# ... or with a block e.g.
#         my $scalar = ${$scalarref};
#         my @array = @{$arrayref};
#         my $hash = %{$hashref};
#         my $sub = &{$subref};
# ... thus
#         @{$arrayref}[0];
#         ${$hashref}{$key};
#         &{$subref}();
# ... or with an arrow e.g.
#         $arrayref->[0];
#         $hashref->{$key};
#         $subref->();
# ... arrow is usually the clearest for element access!
#
# http://perldoc.perl.org/perlstyle.html

#==============================================================================
# Includes
#==============================================================================

#use diagnostics;
use strict;
use warnings;

# persistent database connections; see
# http://perl.apache.org/docs/1.0/guide/databases.html;
# sudo apt-get install libapache-dbi-perl
use Apache::DBI;

# Level 2 shows passwords for reconnect; level 1 shows passwords for
# connect; avoid
$Apache::DBI::DEBUG = 0;

use CGI;
use Config::IniFiles;    # sudo apt-get install libconfig-inifiles-perl

# sudo apt-get install libcrypt-eksblowfish-perl
use Crypt::Eksblowfish::Bcrypt qw(bcrypt);
use Data::Dumper;
local $Data::Dumper::Terse = 1;
use DateTime;
use DateTime::Format::MySQL;
use DBI;                 # sudo apt-get install libdbi-perl
use Digest::SHA qw(sha512_hex);
use List::MoreUtils qw(firstidx);
use MIME::Base64;
use Text::CSV;           # sudo apt-get install libtext-csv-perl
use Time::HiRes;

#==============================================================================
# for mod_perl
#==============================================================================
# "Variable '$x' will not stay shared" errors
#   mod_perl wraps everything in a subroutine
#   http://stackoverflow.com/questions/11006386
# Solution: change file-level variable from "my" to "our"
#   then: EXPLICIT INSTANTIATION NECESSARY, e.g. our @listthing = ();
#         NOT JUST our @listthing;
#   ... otherwise, one instance's variables will merge with another's...

# "Subroutine redefined" messages: means Apache has reloaded the script:
# http://www.gossamer-threads.com/lists/modperl/modperl/88481

no warnings qw(redefine);

# Alternative: Apache::PerlRun
# http://perl.apache.org/docs/1.0/api/Apache/PerlRun.html

# READ THIS: http://perl.apache.org/docs/1.0/guide/porting.html

#==============================================================================
# Constants
#==============================================================================

use constant {

    # Debugging levels:
    DEBUG_BASIC      => 1,
    DEBUG_EXTENDED   => 2,
    DEBUG_VERBOSE    => 3,
    DEBUG_DANGER     => 4,
    DEBUG_RIDICULOUS => 5,

    # Number of ID numbers:
    NUMBER_OF_IDNUMS => 8,

    # Fixed:
    CLIENT_DATE_FIELD         => "when_last_modified",
    MOVE_OFF_TABLET_FIELDNAME => "_move_off_tablet",

    # ... must match DBCONSTANTS.js on the tablet, and cc_constants.py on the
    #     server
    # ... this field is read in transit.
    ERA_NOW => "NOW",
};

# Perl's constant array metaphor is a bit strange
# (http://perldoc.perl.org/constant.html).
# For the moment:

our @reservedtables = (
    "_dirty_tables",              "_dirty_records",
    "_hl7_message_log",           "_hl7_run_log",
    "_security_account_lockouts", "_security_audit",
    "_security_devices",          "_security_login_failures",
    "_security_users",            "_security_webviewer_sessions",
    "_server_storedvars",         "_special_notes"
);

our @reserved_fields = (
    "_pk",                     "_device",
    "_era",                    "_current",
    "_when_added_exact",       "_when_added_batch_utc",
    "_adding_user",            "_when_removed_exact",
    "_when_removed_batch_utc", "_removing_user",
    "_preserving_user",        "_predecessor_pk",
    "_successor_pk",           "_manually_erased",
    "_manually_erased_at",     "_manually_erasing_user",
    "_camcops_version",        "_addition_pending",
    "_removal_pending"
);

#==============================================================================
# CAREFUL ORDER DEPENDENCY IN THIS NEXT SECTION.
# Functions or global variables first?
# - subs first, where they access global variables:
#       moans about not knowing the global variables (subs won't compile)
# - global variables first, but calling subs to define them:
#       "XXX called too early to check prototype" errors
# - uninitialized global variables:
#       explicit instantiation required for mod_perl
# - solution:
#   To call a function before it's defined: prefix the call with &
#   http://alvinalexander.com/perl/call-perl-subroutines-sub-function-ampersand
#==============================================================================

our $starttime_hires = Time::HiRes::time();
our $now_dt_utc      = &epoch_time_to_utc_datetime($starttime_hires);
our $now_dt_local    = &epoch_time_to_local_datetime($starttime_hires);
our $now         = &datetime_to_string($now_dt_local);   # ISO8601 with timezone
our $remote_addr = get_env_var("REMOTE_ADDR");
our $remote_port = get_env_var("REMOTE_PORT");

our @logmessages = ();

&writelog("CamCOPS database script starting at $now");

# Caching in mod_perl:
# http://docstore.mik.ua/orelly/weblinux2/modperl/ch18_01.htm
use vars qw(
  $allow_mobileweb
  $dbname
  $dbpassword
  $db_title
  $dbuser
  $DEBUGLEVEL
  $dsn
  $finalize_policy
  @iddesc
  @idshortdesc
  $upload_policy
  @valid_table_names
);

# Apply mod_perl caching to the retrieval of the configuration variables
# (get_config_vars is an expensive function, taking 5-10 ms).
&get_config_vars() unless $dsn;

# Connect to database (connections cached via Apache::DBI)
if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
    &report_elapsed_time("ABOUT TO OPEN DATABASE");
}
our $dbh = DBI->connect(
    $dsn, $dbuser,
    $dbpassword,
    {
        #PrintError => 1,  # report errors via warn()?
        #RaiseError => 0  # report errors via die()?
        ShowErrorStatement => 1,    # adds the offending SQL to the error msg
        HandleError => \&dbi_error_handler    # custom error-handling function
    }
) || &fail_server_error("Couldn't connect to database: $DBI::errstr");

$dbh->{AutoCommit} = 0;                       # enable transactions, if poss.

if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
    &report_elapsed_time("OPENED DATABASE");
}

# Apply mod_perl caching to @valid_table_names
@valid_table_names = &fetch_valid_table_names() unless @valid_table_names;

#==============================================================================
# Objects
#==============================================================================

our $csv = Text::CSV->new(
    {
        # http://search.cpan.org/~makamaka/Text-CSV-1.21/lib/Text/CSV.pm
        escape_char         => "'",
        quote_char          => "'",
        binary              => 1,     # REQUIRED for embedded newlines
        blank_is_undef      => 1,
        allow_loose_escapes => 1,

        # verbatim => 1,
        quote_space => 0
    }
) or &fail_server_error( "Can't use Text::CSV: " . Text::CSV->error_diag() );

# Embedded newlines: see
# http://search.cpan.org/~makamaka/Text-CSV-1.21/lib/Text/CSV.pm#parse

our $cq = CGI->new;                   # CGI query

#==============================================================================
# Language help
#==============================================================================

sub in_A_not_B {

    # call as in_A_not_B(\@A, \@B)
    my ( $refA, $refB ) = @_;

    # SAFEGUARD EITHER METHOD:
    if ( !@$refA ) {
        return ();    # empty array
    }

    if ( !@$refB ) {
        return @$refA;    # contents of A
    }

    # METHOD 1: BUT OCCASIONAL "Use of uninitialized value $_ in hash element"
    # errors:
    # http://www.perlmonks.org/?node_id=205991

    ## Create a hash representing B
    #my %seen;                         # empty hash
    #$seen{$_} = undef foreach (@$refB);
    ## grep only leaves what evaluates to true.
    ## if an element of A is not in B, it is
    ## left in place
    #return grep { not exists $seen{$_} } @$refA;

    # METHOD 2: BUT OCCASIONAL "Use of uninitialized value in list assignment"
    # instead.
    # http://stackoverflow.com/questions/4891898

    my %in_b = map { $_ => 1 } @$refB;
    return grep { not $in_b{$_} } @$refA;
}

sub array_to_csv_except_undef {
    my ($arrayref) = @_;
    return join( ",", grep( defined, @$arrayref ) );
}

#==============================================================================
# Date
#==============================================================================

sub datetime_to_string {
    my $dt      = shift;
    my $mainbit = $dt->strftime("%Y-%m-%dT%H:%M:%S.%3N");
    my $tz      = $dt->strftime("%z");                      # e.g. "+0000"
         # convert "+0000" to "+00:00"
    my $tz2 = substr( $tz, 0, 3 ) . ":" . substr( $tz, 3, 2 );
    return $mainbit . $tz2;

    # YYYY-MM-DDTHH:mm:ss.SSSZ, e.g. 2012-07-25T16:38:02.257+01:00
    # RFC822-conformant dates (using "%a, %d %b %Y %H:%M:%S %z").
    # http://search.cpan.org/~drolsky/DateTime-0.76/lib/DateTime.pm
}

sub utc_datetime_to_second_precision_string {
    my $dt = shift;
    return $dt->strftime("%Y-%m-%dT%H:%M:%SZ");
}

sub epoch_time_to_local_datetime {
    my $epochtime = shift;
    return DateTime->from_epoch( epoch => $epochtime, time_zone => 'local' );
}

sub epoch_time_to_utc_datetime {
    my $epochtime = shift;
    return DateTime->from_epoch( epoch => $epochtime );
}

# Avoid DateTime->now(); that's equivalent to
#   DateTime->from_epoch(epoch => time())
# with Perl's default time() function, which has a resolution of 1 s.

#==============================================================================
# Environment variables
#==============================================================================

sub get_env_var {
    my ( $var, $mandatory ) = @_;
    $mandatory = 1 unless defined $mandatory;
    my $val = $ENV{$var};
    if ($mandatory) {
        unless ($val) {
            fail_server_error( "Web server configuration wrong - environment "
                  . "variable $var not set" );
        }
    }
    return $val;
}

sub show_all_env_vars {

    # Minimal output; call this on its own.
    foreach my $var ( sort( keys(%ENV) ) ) {
        unless ( $var eq "DB_PASSWORD" ) {    # Security risk otherwise!
            my $val = $ENV{$var};
            $val =~ s/\n/\\n/g;
            $val =~ s/"/\\"/g;
            writelog("${var}=\"${val}\"");
        }
    }
}

sub get_config_vars() {
    my $config_file = get_env_var("CAMCOPS_CONFIG_FILE");

    # &report_elapsed_time("READ CONFIG FILE: START");
    # ... NB can't use $DEBUGLEVEL since it's not been read yet!
    my $cfg = Config::IniFiles->new( -file => $config_file );

    # ... will be undef if unsuccessful
    if ( !defined $cfg ) {
        fail_server_error( "Couldn't read configuration file $config_file\n"
              . "Errors were:\n@Config::IniFiles::errors" );
    }
    my $section = "server";

    # Write back to global variables:
    $dbname          = $cfg->val( $section, "DB_NAME" );
    $dbuser          = $cfg->val( $section, "DB_USER" );
    $dbpassword      = $cfg->val( $section, "DB_PASSWORD" );
    $allow_mobileweb = $cfg->val( $section, "ALLOW_MOBILEWEB", 0 );
    $DEBUGLEVEL      = $cfg->val( $section, "DATABASE_DEBUG_OUTPUT", 1 );

    # The next line assumes the use of MySQL.
    $dsn = "DBI:mysql:" . $dbname . ";mysql_enable_utf8=1";
    $db_title = $cfg->val( $section, "DATABASE_TITLE" );
    for ( my $i = 1 ; $i <= NUMBER_OF_IDNUMS ; $i++ ) {
        $iddesc[$i]      = $cfg->val( $section, "IDDESC_$i" );
        $idshortdesc[$i] = $cfg->val( $section, "IDSHORTDESC_$i" );
    }
    $upload_policy   = $cfg->val( $section, "UPLOAD_POLICY" );
    $finalize_policy = $cfg->val( $section, "FINALIZE_POLICY" );
    if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
        &report_elapsed_time("READ CONFIG FILE: END");
    }
}

#==============================================================================
# Logging, exiting
#==============================================================================

sub writelog {
    push( @logmessages, @_ ) if (@_);
}

sub send_log {
    print("(camcopsdb) $logmessages[0]\n") if ( $#logmessages >= 0 );

    # ... first line not indented
    foreach ( @logmessages[ 1 .. $#logmessages ] ) {

        # second to last elements; works even if array size <2
        print("  (camcopsdb) $_\n");
    }
}

sub send_log_stderr {
    print( STDERR "(camcopsdb) $logmessages[0]\n" ) if ( $#logmessages >= 0 );

    # ... first line not indented
    foreach ( @logmessages[ 1 .. $#logmessages ] ) {

        # second to last elements; works even if array size <2
        print( STDERR "  (camcopsdb) $_\n" );
    }
}

sub report_elapsed_time {
    my ($msg)            = @_;
    my $time_hires       = Time::HiRes::time();
    my $elapsed_time_sec = $time_hires - $starttime_hires;
    writelog( $msg . " - ELAPSED TIME (s): " . $elapsed_time_sec );
}

sub finish {

    # Header, with a status code, content type, and two newlines at the end.
    my ( $status, $reply ) = @_;
    my $finishtime_hires   = Time::HiRes::time();
    my $execution_time_sec = $finishtime_hires - $starttime_hires;
    writelog( "CamCOPS database script finishing; took "
          . $execution_time_sec
          . " s" );
    print("Status: $status\n");
    print("Content-Type: text/plain\n\n");

    # Apache appends the Content-Length.
    if ( defined($reply) ) {
        print($reply);
    }
    else {
        send_log();
    }
}

sub succeed {
    my ( $logmsg, $reply ) = @_;
    writelog($logmsg);
    finish( "200 OK", "Success:1\n$reply" );

    # ... see fail_user_error for explanation
    # For debugging:
    send_log_stderr() if ( $DEBUGLEVEL >= DEBUG_BASIC );

    # ... so it also appears in the HTTPD log
    $dbh->commit;
    exit 0;
}

sub succeed_generic {
    my ($operation) = @_;
    succeed( "CamCOPS: $operation", $operation );
}

sub fail_user_error {

    # While Titanium-Android can extract error messages from e.g.
    # finish("400 Bad Request: @_"), Titanium-iOS can't, and we need the error
    # messages. Therefore, we will return an HTTP success code but "Success: 0"
    # in the reply details.
    writelog( "CLIENT-SIDE SCRIPT ERROR", @_ );
    finish( "200 OK", "Success:0\nError:@_" );
    send_log_stderr() if ( $DEBUGLEVEL >= DEBUG_BASIC );

    # ... so it also appears in the HTTPD log
    $dbh->commit;
    exit 0;
}

sub fail_server_error {
    writelog( "SERVER-SIDE SCRIPT ERROR", @_ );
    finish( "503 Database Unavailable: @_", "Success:0\nError:@_" );
    send_log_stderr();    # so it also appears in the HTTPD log
    $dbh->rollback;
    exit 1;
}

#==============================================================================
# Database handling
#==============================================================================

sub dbi_error_handler {
    my ( $message, $handle, $first_value ) = @_;
    fail_server_error("Database error: $message");
}

#==============================================================================
# CGI input functions
#==============================================================================

sub ensure_method_is_post {
    $ENV{"REQUEST_METHOD"} =~ tr/a-z/A_Z/;    # make upper case
    if ( $ENV{"REQUEST_METHOD"} ne "POST" ) {
        fail_user_error("Must use POST method");
    }
}

sub show_all_post_vars() {

    # Minimal output; call this on its own.
    my @names = $cq->param;
    foreach my $name ( sort(@names) ) {
        my $value = $cq->param($name);
        writelog("POST: ${name}=${value}");
    }
}

sub get_post_var {
    my ( $var, $mandatory ) = @_;
    $mandatory = 1 unless defined $mandatory;
    my $val = $cq->param($var);
    if ($mandatory) {
        unless ( defined $val ) {
            fail_user_error("Must provide the variable: $var");
        }
    }
    return $val;
}

#==============================================================================
# Conversion to/from quoted SQL values
#==============================================================================

sub decode_single_value {
    my ($v) = @_;

    #writelog("incoming value: $v"); # debugging only
    if ( !defined($v) || $v =~ /^NULL$/i || length($v) == 0 ) # case-insensitive
    {
        #writelog("NULL found"); # debugging only
        # NULL: replace with a code indicating a proper NULL (or we'll insert
        # the string "NULL")
        return undef;
    }

    # Assign v to vtrimmed, then replace whitespace with nothing
    # We remove whitespace in some cases because some base-64 encoders insert
    # newline characters (e.g. Titanium iOS).
    ( my $vtrimmed = $v ) =~ s/\s//g;

    if (
        $vtrimmed =~ m/
            ^X'                       (?# begins with X')
            ([a-fA-F0-9][a-fA-F0-9])+ (?# one or more hex pairs)
            '$                        (?# ends with ')
         /x
      )    # the x allows whitespace/comments in the regex
    {
        #writelog("BLOB FOUND: hex encoding"); # debugging only
        # SPECIAL HANDLING for BLOBs: a string like X'01FF' means a hex-encoded
        # BLOB
        # ... because Titanium is rubbish at blobs, so we encode them as
        # special string literals.
        # Hex-encoded BLOB, like X'CDE7A24B1A9DBA3148BCB7A0B9DA5BB6A424486C'
        # Strip off the start and end:
        $vtrimmed = substr( $vtrimmed, 2, length($vtrimmed) - 3 );

        $vtrimmed =~ s/([a-fA-F0-9][a-fA-F0-9])/chr(hex($1))/eg;

        # or pack: http://stackoverflow.com/questions/2427527
        # Perl strings can contain zero/null bytes:
        #     http://docstore.mik.ua/orelly/perl/cookbook/ch01_01.htm
        # BLOBs to/from to the database:
        #     http://www.james.rcpt.to/programs/mysql/blob/
        return $vtrimmed;
    }
    if (
        $vtrimmed =~ m{
            ^64'
            (?: [A-Za-z0-9+/]{4} )*        (?# zero or more quads, followed by)
            (?:
                [A-Za-z0-9+/]{2} [AEIMQUYcgkosw048] = (?# a triple then an =)
            |                                         (?# ... or...)
                [A-Za-z0-9+/] [AQgw] ==               (?# a pair then ==)
            )?
            '$
        }x
      )
    {
        #writelog("BLOB FOUND: base64 encoding"); # debugging only
        # OTHER WAY OF DOING BLOBS: base64 encoding
        # e.g. a string like 64'cGxlYXN1cmUu' is a base-64-encoded BLOB
        # (the 64'...' bit is my representation)
        # regex from http://stackoverflow.com/questions/475074
        # better one from http://www.perlmonks.org/?node_id=775820
        #writelog("BLOBSTRING: LEFT: " . substr($v, 0, 10));
        #writelog("BLOBSTRING: RIGHT: " . substr($v, -10));
        # Strip off the start and end:
        $vtrimmed = substr( $vtrimmed, 3, length($vtrimmed) - 4 );

        #writelog("STRIPPED BLOBSTRING: LEFT: " . substr($v, 0, 10));
        #writelog("STRIPPED BLOBSTRING: RIGHT: " . substr($v, -10));
        $vtrimmed = decode_base64($vtrimmed);

        #writelog("BLOB: LEFT: " . substr($v, 0, 10));
        #writelog("BLOB: RIGHT: " . substr($v, -10));
        return $vtrimmed;
    }

    # Strings are handled by Text::CSV and its escape/quote characters.
    # Numbers are handled automatically by Perl.
    #writelog("value: $v"); # debugging only
    return $v;
}

sub encode_single_value {
    my ( $v, $isblob ) = @_;
    if ($isblob) {
        return "'64''" + encode_base64($v) + "'''";

        # send 64'xxx' by quote-encoding to '64''xxx'''
    }
    return $dbh->quote($v);

    # ... returns NULL for undef
    # ... appropriately quotes strings
}

sub decode_values {
    my ($valuelist) = @_;
    my $status = $csv->parse($valuelist);
    if ( !$status ) {
        my $err = $csv->error_input;
        fail_user_error("Failed to parse line: $err");
    }
    my @values = $csv->fields();

    #writelog("VALUELIST: $valuelist"); # debugging only
    #writelog("VALUE ARRAY: @values"); # debugging only
    foreach my $v (@values) {

        # modifying $v modifies the array
        $v = decode_single_value($v);
    }

    # Re binding, see http://docstore.mik.ua/orelly/linux/dbi/ch05_03.htm
    return @values;
}

sub get_single_field_from_post_var {
    my ($postvar) = @_;
    my $field = get_post_var( $postvar, 1 );    # always mandatory
    ensure_valid_field_name($field);
    return $field;
}

sub get_fields_from_post_var {
    my ( $postvar, $mandatory ) = @_;
    $mandatory = 1 unless defined $mandatory;
    my $fieldlist = get_post_var( $postvar, $mandatory );
    my @fields;                                 # empty array by default
    if ( defined $fieldlist ) {
        @fields = split( ',', $fieldlist );

        # can't have any commas in fields, so it's OK to use a simple
        # split() command
        foreach my $field (@fields) {
            ensure_valid_field_name($field);
        }
    }
    return @fields;
}

sub get_values_from_post_var {
    my ( $postvar, $mandatory ) = @_;

    # Allows an empty input (e.g. for "which_keys_to_send")
    $mandatory = 1 unless defined $mandatory;
    my $recvalues = get_post_var( $postvar, $mandatory );

    #writelog("record $r: $recvalues"); # debugging only
    my @values;    # empty array by default
    if ( defined $recvalues ) {
        @values = decode_values($recvalues);
    }
    return @values;
}

sub get_fields_and_values {
    my ( $fields_post_var, $values_post_var, $mandatory ) = @_;
    $mandatory = 1 unless defined $mandatory;
    my @fields  = get_fields_from_post_var( $fields_post_var, $mandatory );
    my $nfields = scalar(@fields);
    my @values  = get_values_from_post_var( $values_post_var, $mandatory );
    my $nvalues = scalar(@values);
    if ( $nfields != $nvalues ) {
        fail_user_error( "Number of fields ($nfields) doesn't match number of "
              . "values ($nvalues)" );
    }
    my %hash;
    @hash{@fields} = @values;
    return %hash;
}

sub get_tables_from_post_var {
    my ( $postvar, $mandatory ) = @_;
    $mandatory = 1 unless defined $mandatory;
    my $tablelist = get_post_var( $postvar, $mandatory );
    my @tables;    # empty array by default
    if ( defined $tablelist ) {
        @tables = split( ',', $tablelist );

        # can't have any commas in table names, so it's OK to use a simple
        # split() command
        foreach my $table (@tables) {
            ensure_valid_table_name($table);
        }
    }
    return @tables;
}

#==============================================================================
# CamCOPS table functions
#==============================================================================

sub fetch_valid_table_names {

    # uses global @valid_table_names
    my $query = "SELECT table_name FROM information_schema.tables "
      . "WHERE table_schema=?;";
    my $sth = $dbh->prepare($query);    # sth: statement handle
    $sth->execute($dbname);
    my @valid_table_names = ();
    while ( my @rowarray = $sth->fetchrow_array() ) {
        push( @valid_table_names, $rowarray[0] );
    }
    return @valid_table_names;
}

sub ensure_valid_table_name {
    my ($table) = @_;

    # Free from SQL injection problems?
    if ( $table =~ m/[^a-zA-Z0-9_]/ ) {
        fail_user_error("Table name contains invalid characters: $table");
    }

    # Not a reserved table name?
    if ( grep { /^$table$/ } @reservedtables ) {
        fail_user_error(
            "Invalid attempt to write to a reserved table: " . "$table" );
    }

    # Table exists?
    if ( grep { /^$table$/ } @valid_table_names ) {

        # Found it; that's OK.
        return;
    }
    fail_user_error("Table doesn't exist on the server: $table");
}

sub ensure_valid_field_name {
    my ($field) = @_;

    # Free from SQL injection problems?
    if ( $field =~ m/[^a-zA-Z0-9_]/ ) {
        fail_user_error("Field name contains invalid characters: $field");
    }

    # Not a reserved field name?
    if ( grep { /^$field$/ } @reserved_fields ) {
        fail_user_error(
            "Invalid attempt to access a reserved field name: " . "$field" );
    }
}

sub get_server_pks_of_active_records {
    my ( $table, $device ) = @_;
    my $query =
        "SELECT _pk FROM $table "
      . "WHERE _device=? AND _current AND _era='"
      . ERA_NOW . "'";
    my $sth = $dbh->prepare($query);
    $sth->execute($device);
    my @pkarray;
    while ( my @rowarray = $sth->fetchrow_array() ) {
        push( @pkarray, $rowarray[0] );
    }
    return @pkarray;
}

sub record_exists {
    my ( $device, $table, $clientpk_name, $clientpk_value ) = @_;
    my $query =
        "SELECT _pk FROM $table "
      . "WHERE _device=? AND _current AND _era='"
      . ERA_NOW
      . "' AND $clientpk_name=?";
    my $sth = $dbh->prepare($query);
    $sth->execute( $device, $clientpk_value );
    my $found = 0;    # no native true/false types in Perl
    my $serverpk;     # initially undef
    if ( ($serverpk) = $sth->fetchrow_array() ) {
        $found = 1;

        # Consider a warning/failure if we have >1 row meeting these criteria.
        # Not currently checked for.
    }
    return ( $found, $serverpk );
}

sub get_server_pks_of_specified_records {
    my ( $device, $table, $wherehashref ) = @_;
    my $query =
        "SELECT _pk FROM $table "
      . "WHERE _device=? AND _current AND _era='"
      . ERA_NOW . "'";
    foreach my $wherefield ( keys %$wherehashref ) {
        $query .= " AND " . delimitfield($wherefield) . "=?";
    }
    my $sth   = $dbh->prepare($query);
    my $param = 1;
    $sth->bind_param( $param++, $device );
    foreach my $wherevalue ( values %$wherehashref ) {
        $sth->bind_param( $param++, $wherevalue );
    }
    $sth->execute();
    my @pkarray;
    while ( my @rowarray = $sth->fetchrow_array() ) {
        push( @pkarray, $rowarray[0] );
    }
    return @pkarray;
}

sub append_where_sql_and_values {
    my ( $query, $wherehashref, $wherenothashref, @values ) = @_;
    my $val;
    my $field;
    if ( defined $wherehashref ) {
        foreach $field ( keys %$wherehashref ) {
            $val = $wherehashref->{$field};
            if ( defined $val ) {
                $query .= " AND " . delimitfield($field) . "=?";
                push( @values, $val );
            }
            else {
                $query .= " AND " . delimitfield($field) . " IS NULL";
            }
        }
    }
    if ( defined $wherenothashref ) {
        foreach $field ( keys %$wherenothashref ) {
            $val = $wherenothashref->{$field};
            if ( defined $val ) {
                $query .= " AND " . delimitfield($field) . "<>?";
                push( @values, $val );
            }
            else {
                $query .= " AND " . delimitfield($field) . " IS NOT NULL";
            }
        }
    }
    return ( $query, @values );
}

sub count_records {
    my ( $device, $table, $wherehashref, $wherenothashref ) = @_;
    my $query =
        "SELECT COUNT(*) FROM $table "
      . "WHERE _device=? AND _current AND _era='"
      . ERA_NOW . "'";
    my @values = ($device);
    ( $query, @values ) = append_where_sql_and_values( $query, $wherehashref,
        $wherenothashref, @values );
    return $dbh->selectrow_array( $query, undef, @values );

    # Standard SELECT COUNT() metaphor:
    # http://stackoverflow.com/questions/1656748
}

sub select_records_with_specified_fields {
    my ( $device, $table, $wherehashref, $wherenothashref, @fields ) = @_;
    my $fieldlist = join( ",", @fields );
    my $query =
        "SELECT $fieldlist FROM $table "
      . "WHERE _device=? AND _current AND _era='"
      . ERA_NOW . "'";
    my @values = ($device);
    ( $query, @values ) = append_where_sql_and_values( $query, $wherehashref,
        $wherenothashref, @values );
    my $sth = $dbh->prepare($query);
    $sth->execute(@values);

    my @final_values;
    my $nrecords = 0;
    while ( my @values = $sth->fetchrow_array() ) {
        push( @final_values, @values );
        ++$nrecords;
    }
    return ( $nrecords, @final_values );
}

sub get_max_client_pk {
    my ( $device, $table, $clientpk_name ) = @_;
    return $dbh->selectrow_array(
        "SELECT MAX($clientpk_name) FROM $table "
          . "WHERE _device=? AND _current AND _era='"
          . ERA_NOW . "'",
        undef, $device
    );    # only one row, only one column
}

sub webclient_delete_records {

    # one-step deletion
    my ( $device, $user, $table, $wherehashref ) = @_;
    my $query =
        "UPDATE $table SET _successor_pk=NULL, _current=0, "
      . "_removal_pending=0, _removing_user=?, "
      . "_when_removed_exact=?, _when_removed_batch_utc=? "
      . "WHERE _device=? AND _current AND _era='"
      . ERA_NOW . "'";
    my @values = ( $user, $now, $now_dt_utc, $device );
    ( $query, @values ) =
      append_where_sql_and_values( $query, $wherehashref, undef, @values );
    $dbh->do( $query, undef, @values );
}

sub record_identical_full    # currently unused
{
    my ( $table, $serverpk, $hashref ) = @_;
    my $query = "SELECT COUNT(*) FROM $table WHERE _pk=?";
    foreach my $field ( delimitfields( keys %$hashref ) ) {
        $query .= " AND $field=?";
    }
    my $sth   = $dbh->prepare($query);
    my $param = 1;
    $sth->bind_param( $param++, $serverpk );
    foreach my $value ( values %$hashref ) {
        $sth->bind_param( $param++, $value );
    }
    $sth->execute();
    my $count = $sth->fetchrow_array();    # only one row, only one column
    return ( $count > 0 );
}

sub record_identical_by_date {
    my ( $table, $serverpk, $client_date_value ) = @_;
    my $count = $dbh->selectrow_array(
        "SELECT COUNT(*) FROM $table WHERE _pk=? AND "
          . CLIENT_DATE_FIELD . "=?",
        undef, $serverpk, $client_date_value
    );                                     # only one row, only one column
    return ( $count > 0 );
}

sub upload_record {

    # Deals with IDENTICAL, MODIFIED, and NEW conditions.
    # (ABSENT is handled by the calling code.)
    my ( $device, $table, $clientpk_name, $hashref, $recordnum,
        $camcops_version )
      = @_;
    my $clientpk_value = $hashref->{$clientpk_name};
    my ( $found, $oldserverpk ) =
      record_exists( $device, $table, $clientpk_name, $clientpk_value );
    my $newserverpk;    # initially undef
    if ($found) {
        my $client_date_value = $hashref->{ CLIENT_DATE_FIELD() };

        # ... brackets or + required in hash lookup by constant:
        # http://perldoc.perl.org/constant.html
        if (
            record_identical_by_date(
                $table, $oldserverpk, $client_date_value
            )
          )
        {
            # IDENTICAL. No action needed...
            # UNLESS MOVE_OFF_TABLET_FIELDNAME is set
            if ( $hashref->{ MOVE_OFF_TABLET_FIELDNAME() } ) {
                flag_record_for_preservation( $table, $oldserverpk );
                if ( $DEBUGLEVEL >= DEBUG_EXTENDED ) {
                    writelog( "Table $table, record $recordnum: identical but "
                          . "moving off tablet" );
                }
            }
            else {
                if ( $DEBUGLEVEL >= DEBUG_EXTENDED ) {
                    writelog("Table $table, record $recordnum: identical");
                }
            }

        }
        else {
            # MODIFIED
            $newserverpk = insert_record( $device, $table, $hashref,
                $oldserverpk, $camcops_version );
            flag_modified( $device, $table, $oldserverpk, $newserverpk );
            if ( $DEBUGLEVEL >= DEBUG_BASIC ) {
                writelog("Table $table, record $recordnum: modified");
            }
        }
    }
    else {
        # NEW
        $newserverpk =
          insert_record( $device, $table, $hashref, undef, $camcops_version );
        if ( $DEBUGLEVEL >= DEBUG_BASIC ) {
            writelog("Table $table, record $recordnum: new");
        }
    }

    return ( $oldserverpk, $newserverpk );
}

sub delimitfield {
    my ($field) = @_;
    return "`$field`";    # MySQL uses back-tick field delimiters
}

sub delimitfields {
    my (@fields) = @_;
    foreach (@fields) {
        $_ = "`$_`";      # MySQL uses back-tick field delimiters
    }
    return @fields;
}

sub insert_record {
    my ( $device, $table, $hashref, $predecessor_pk, $camcops_version ) = @_;
    mark_table_dirty( $device, $table );
    my @fields = (
        "_device",          "_era",
        "_current",         "_addition_pending",
        "_removal_pending", "_predecessor_pk",
        "_camcops_version"
    );
    my @values = (
        $device,
        ERA_NOW,            # _era = 'NOW'
        0,                  # _current
        1,                  # _addition_pending
        0,                  # _removal_pending
        $predecessor_pk,    # _predecessor_pk (may be NULL or valid)
        $camcops_version
    );
    push( @fields, delimitfields( keys %$hashref ) )
      ;                     # append passed field names
    push( @values, values %$hashref );    # append passed values
    my $query =
        "INSERT INTO $table ("
      . join( ",", @fields )
      . ") VALUES ("
      . join( ",", ("?") x ( scalar @values ) ) . ")";

    #writelog("QUERY " . $query);
    my $sth = $dbh->prepare($query);
    $sth->execute(@values);
    return $sth->{'mysql_insertid'};      # MySQL-specific
}

sub duplicate_record {
    my ( $device, $table, $serverpk ) = @_;
    mark_table_dirty( $device, $table );

    # Fetch the existing record
    my $sth = $dbh->prepare("SELECT * FROM $table WHERE _pk=?");
    $sth->execute($serverpk);
    my @values = $sth->fetchrow_array();    # only one row
    my @fields = @{ $sth->{NAME} };

    # ... consider NAME_lc for lower-case, but try this first
    # Remove the PK from what we insert back (that will be autogenerated)
    my $pkfield_index = firstidx { $_ eq "_pk" } @fields;    # List::MoreUtils
    splice( @fields, $pkfield_index, 1 );
    my $nfields = scalar(@fields);
    splice( @values, $pkfield_index, 1 );

    # Perform the insert
    my $insertquery =
        "INSERT INTO $table ("
      . join( ",", delimitfields(@fields) )
      . ") VALUES ("
      . join( ",", ("?") x $nfields ) . ")";
    $sth = $dbh->prepare($insertquery);
    $sth->execute(@values);
    return $sth->{'mysql_insertid'};    # MySQL-specific
        # The resulting record NEEDS MODIFICATION by update_new_copy_of_record
}

sub update_new_copy_of_record {
    my ( $table, $serverpk, $hashref, $predecessor_pk, $camcops_version ) = @_;
    my $query = "UPDATE $table SET _current=0, _addition_pending=1, "
      . "_predecessor_pk=?, _camcops_version=?";
    my @values = ( $predecessor_pk, $camcops_version );
    foreach my $field ( keys %$hashref ) {
        my $df = delimitfield($field);
        $query .= ", $df=?";
        push( @values, $hashref->{$field} );
    }
    $query .= " WHERE _pk=?";
    push( @values, $serverpk );
    $dbh->do( $query, undef, @values );
}

#==============================================================================
# Batch (atomic) upload ad preserving
#==============================================================================

sub get_device_upload_batch_details {
    my ( $device, $user ) = @_;
    my ( $upload_batch_utc, $uploading_user, $currently_preserving ) =
      $dbh->selectrow_array(
        "SELECT ongoing_upload_batch_utc, uploading_user, currently_preserving"
          . " FROM _security_devices WHERE device=?",
        undef, $device
      );    # only one row
    if ( !defined $upload_batch_utc || $uploading_user ne $user ) {

        # SIDE EFFECT: if the username changes, we restart (and thus roll back
        # previous pending changes)
        start_device_upload_batch( $device, $user );
        return $now_dt_utc;
    }

    # DBI DATETIME field to Perl DateTime object...
    # See also http://www.perlmonks.org/?node_id=374655
    $upload_batch_utc =
      DateTime::Format::MySQL->parse_datetime($upload_batch_utc)
      ;    # convert from ?string ?numeric to DateTime
    return ( $upload_batch_utc, $currently_preserving );
}

sub start_device_upload_batch {
    my ( $device, $user ) = @_;
    rollback_all($device);
    $dbh->do(
        "UPDATE _security_devices SET last_upload_batch_utc=?, "
          . "ongoing_upload_batch_utc=?, uploading_user=? WHERE device=?",
        undef, $now_dt_utc, $now_dt_utc, $user, $device
    );
}

sub end_device_upload_batch {
    my ( $device, $user, $batchtime, $preserving ) = @_;
    commit_all( $device, $user, $batchtime, $preserving );
    $dbh->do(
        "UPDATE _security_devices SET ongoing_upload_batch_utc=NULL, "
          . "uploading_user=NULL, currently_preserving=0 WHERE device=?",
        undef, $device
    );
}

sub start_preserving {
    my ($device) = @_;
    $dbh->do(
        "UPDATE _security_devices SET currently_preserving=1 WHERE device=?",
        undef, $device );
}

sub mark_table_dirty {

    # This table has a joint primary key, so there can only be one row for a
    # given device/tablename combination.
    my ( $device, $tablename ) = @_;
    $dbh->do(
        "REPLACE INTO _dirty_tables (device, tablename) VALUES (?,?)",

        # http://dev.mysql.com/doc/refman/5.0/en/replace.html
        undef,
        $device, $tablename
    );
}

sub get_dirty_tables {
    my ($device) = @_;
    my $query    = "SELECT tablename FROM _dirty_tables WHERE device=?";
    my $sth      = $dbh->prepare($query);
    $sth->execute($device);
    my @tables;
    while ( my @rowarray = $sth->fetchrow_array() ) {
        push( @tables, $rowarray[0] );
    }
    return @tables;
}

sub flag_deleted {
    my ( $device, $table, @pks ) = @_;
    mark_table_dirty( $device, $table );
    my $query = "UPDATE $table SET _removal_pending=1, _successor_pk=NULL "
      . "WHERE _pk=?";

    # MySQL: zero is false, nonzero is true
    my $sth = $dbh->prepare($query);
    foreach my $pk (@pks) {
        $sth->execute($pk);
    }
}

sub flag_all_records_deleted {
    my ( $device, $table ) = @_;
    mark_table_dirty( $device, $table );
    $dbh->do(
        "UPDATE $table SET _removal_pending=1, _successor_pk=NULL "
          . "WHERE _device=?",
        undef, $device
    );
}

sub flag_deleted_where_clientpk_not {
    my ( $device, $table, $clientpk_name, @clientpk_values ) = @_;
    mark_table_dirty( $device, $table );
    my @wherelist;
    my $query =
        "UPDATE $table SET _removal_pending=1, _successor_pk=NULL "
      . "WHERE _device=? AND _current AND _era='"
      . ERA_NOW . "'";
    my @params = ($device);
    if ( scalar(@clientpk_values) > 0 ) {
        foreach my $clientpk_value (@clientpk_values) {
            push( @wherelist, $clientpk_name . "=?" );
            push( @params,    $clientpk_value );
        }
        $query .= " AND NOT(" . join( " OR ", @wherelist ) . ")";
    }
    $dbh->do( $query, undef, @params );
}

sub flag_modified {
    my ( $device, $table, $pk, $successor_pk ) = @_;
    mark_table_dirty( $device, $table );
    $dbh->do(
        "UPDATE $table SET _removal_pending=1, _successor_pk=? WHERE _pk=?",
        undef, $successor_pk, $pk );
}

sub flag_record_for_preservation {
    my ( $table, $pk ) = @_;
    $dbh->do(
        "UPDATE $table SET " . MOVE_OFF_TABLET_FIELDNAME . "=1 WHERE _pk=?",
        undef, $pk );
}

sub commit_all {
    my ( $device, $user, $batchtime, $preserving ) = @_;
    my @tables = get_dirty_tables($device);
    my ( $n_added, $n_removed, $n_preserved );
    my @auditsegments;
    foreach my $table (@tables) {
        ( $n_added, $n_removed, $n_preserved ) =
          commit_table( $device, $user, $batchtime, $preserving, $table );
        push( @auditsegments, "$table ($n_added,$n_removed,$n_preserved)" );
    }
    clear_dirty_tables($device);
    audit( $user, $device, undef, undef,
        "Upload [table (n_added,n_removed,n_preserved)]: "
          . join( ", ", @auditsegments ) );
}

sub commit_table {
    my ( $device, $user, $batchtime, $preserving, $table, $clear_dirty ) = @_;
    my $n_added = $dbh->do(
        "UPDATE $table SET _current=1, _addition_pending=0, _adding_user=?, "
          . "_when_added_exact=?, _when_added_batch_utc=? "
          . "WHERE _device=? AND _addition_pending",
        undef, $user, $now, $batchtime, $device
    );
    my $n_removed = $dbh->do(
        "UPDATE $table SET _current=0, _removal_pending=0, _removing_user=?, "
          . "_when_removed_exact=?, _when_removed_batch_utc=? "
          . "WHERE _device=? AND _removal_pending",
        undef, $user, $now, $batchtime, $device
    );
    my $new_era = utc_datetime_to_second_precision_string($batchtime);
    my $n_preserved;
    if ($preserving) {

        # Preserve all relevant records
        $n_preserved = $dbh->do(
            "UPDATE $table SET _era=?, _preserving_user=?, "
              . MOVE_OFF_TABLET_FIELDNAME . "=0 "
              . "WHERE _device=? AND _era='"
              . ERA_NOW . "'",
            undef, $new_era, $user, $device
        );
    }
    else {
        # Preserve any individual records
        $n_preserved = $dbh->do(
            "UPDATE $table SET _era=?, _preserving_user=?, "
              . MOVE_OFF_TABLET_FIELDNAME . "=0 "
              . "WHERE _device=? AND "
              . MOVE_OFF_TABLET_FIELDNAME,
            undef, $new_era, $user, $device
        );
    }
    if ($clear_dirty) {
        $dbh->do( "DELETE FROM _dirty_tables WHERE device=? AND tablename=?",
            undef, $device, $table );

        # ... otherwise a call to clear_dirty_tables() must be made.
    }

    # DBI returns "0E0" as a zero-but-true value. So:
    $n_added     = 0 if ( $n_added     eq "0E0" );
    $n_removed   = 0 if ( $n_removed   eq "0E0" );
    $n_preserved = 0 if ( $n_preserved eq "0E0" );
    return ( $n_added, $n_removed, $n_preserved );
}

sub rollback_all {
    my ($device) = @_;
    my @tables = get_dirty_tables($device);
    foreach my $table (@tables) {
        rollback_table( $device, $table );
    }
    clear_dirty_tables($device);
}

sub rollback_table {
    my ( $device, $table ) = @_;
    $dbh->do( "DELETE FROM $table WHERE _device=? AND _addition_pending",
        undef, $device );
    $dbh->do(
        "UPDATE $table SET _removal_pending=0, _when_removed_exact=NULL, "
          . "_when_removed_batch_utc=NULL, _removing_user=NULL, "
          . "_successor_pk=NULL WHERE _device=? AND _removal_pending",
        undef, $device
    );
}

sub clear_dirty_tables {
    my ($device) = @_;
    $dbh->do( "DELETE FROM _dirty_tables WHERE device=?", undef, $device );
}

#==============================================================================
# Audit trail
#==============================================================================

sub where_clause_for_audit {
    my ($wherehashref) = @_;
    my @wherebits;
    keys %$wherehashref;

    # reset internal iterator: http://stackoverflow.com/questions/3033
    while ( my ( $k, $v ) = each %$wherehashref ) {
        push( @wherebits, "$k=$v" );

        # would be unsafe as SQL (injection, not delimited) but tolerable for
        # audit purposes only
    }
    return join( " AND ", @wherebits );
}

sub where_not_clause_for_audit {
    my ($wherehashref) = @_;
    my @wherebits;
    keys %$wherehashref;

    # reset internal iterator: http://stackoverflow.com/questions/3033
    while ( my ( $k, $v ) = each %$wherehashref ) {
        push( @wherebits, "$k<>$v" );

        # would be unsafe as SQL (injection) but tolerable for audit purposes
        # only
    }
    return join( " AND ", @wherebits );
}

sub audit {
    my ( $user, $device, $table, $server_pk, $details ) = @_;
    $dbh->do(
        "INSERT INTO _security_audit (when_access_utc, source, remote_addr, "
          . "user, device, table_name, server_pk, patient_server_pk, details) "
          . "VALUES (?,?,?,?,?,?,?,?,?)",
        undef,
        $now_dt_utc,
        "tablet",
        $remote_addr,
        $user,
        $device,
        $table,
        $server_pk,
        undef,
        $details
    );
}

#==============================================================================
# User validation and device registration
#==============================================================================

sub is_password_valid {

    # bcrypt
    # - http://search.cpan.org/~zefram/Crypt-Eksblowfish-0.008/lib/Crypt/
    #          Eksblowfish/Bcrypt.pm
    # - the hashed password BEGINS WITH its settings

    my ( $plain_password, $hashed_password ) = @_;
    if ( !$hashed_password ) {
        return 0;    # sad
    }
    return ( $hashed_password eq bcrypt( $plain_password, $hashed_password ) );
}

sub ensure_valid_user_for_device_registration {
    my ( $user, $password ) = @_;
    my $query = "SELECT hashedpw FROM _security_users "
      . "WHERE user=? AND may_register_devices";
    my $sth = $dbh->prepare($query);
    $sth->execute($user)
      or fail_server_error(
        "Couldn't check security " . "credentials: $sth->errstr" );
    my $hashedpw;
    if (   !( ($hashedpw) = $sth->fetchrow_array() )
        || !is_password_valid( $password, $hashedpw ) )
    {
        fail_user_error("Invalid username/password");    # sad
    }
    return;                                              # happy
}

sub ensure_valid_user_for_webstorage {

    # mobileweb storage is per-user; the device is "mobileweb_USERNAME".
    my ( $device, $user, $password ) = @_;
    if ( $device ne ( "mobileweb_" . $user ) ) {
        fail_user_error("Mobileweb device doesn't match username");    # sad
    }
    my $query = "SELECT hashedpw FROM _security_users "
      . "WHERE user=? AND may_use_webstorage";
    my $sth = $dbh->prepare($query);
    $sth->execute($user)
      or fail_server_error(
        "Couldn't check security " . "credentials: $sth->errstr" );
    my $hashedpw;
    if (   !( ($hashedpw) = $sth->fetchrow_array() )
        || !is_password_valid( $password, $hashedpw ) )
    {
        fail_user_error("Invalid username/password");                  # sad
    }
    return;                                                            # happy
}

sub register_device {
    my ( $device, $user, $device_friendly_name, $camcops_version ) = @_;
    my $count = $dbh->selectrow_array(
        "SELECT COUNT(*) FROM _security_devices WHERE device=?",
        undef, $device );    # only one row, only one column
    if ( $count > 0 ) {

        # device already registered, but accept re-registration
        $dbh->do(
            "UPDATE _security_devices SET friendly_name=?, camcops_version=?, "
              . "registered_by_user=?, when_registered_utc=? WHERE device=?",
            undef,
            $device_friendly_name,
            $camcops_version,
            $user,
            $now_dt_utc,
            $device
          )
          ; # http://stackoverflow.com/questions/20910816/why-does-perl-dbi-require-a-prepare-statement-before-execution
    }
    else {
        # new registration
        $dbh->do(
            "INSERT INTO _security_devices (device, friendly_name, "
              . "camcops_version, registered_by_user, when_registered_utc) "
              . "VALUES (?, ?, ?, ?, ?)",
            undef,
            $device,
            $device_friendly_name,
            $camcops_version,
            $user,
            $now_dt_utc
        );
    }
}

sub check_device_registered {
    my ($device) = @_;
    if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
        report_elapsed_time("check_device_registered starting");
    }
    my $count = $dbh->selectrow_array(
        "SELECT COUNT(*) FROM _security_devices WHERE device=?",
        undef, $device );    # only one row, only one column
    fail_user_error("Unregistered device") if ( $count == 0 );

    # Device is registered.
}

sub ensure_valid_device_and_user_for_uploading {
    my ( $user, $password, $device ) = @_;
    if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
        report_elapsed_time( "ensure_valid_device_and_user_for_uploading: "
              . "validating user (NB bcrypt is meant to be "
              . "slow!)" );
    }
    my $query =
      "SELECT hashedpw, may_upload FROM _security_users " . "WHERE user=?";
    my $sth = $dbh->prepare($query);
    $sth->execute($user)
      or fail_server_error(
        "Couldn't check security " . "credentials: $sth->errstr" );
    my ( $hashedpw, $may_upload );
    if (   !( ( $hashedpw, $may_upload ) = $sth->fetchrow_array() )
        || !$may_upload
        || !is_password_valid( $password, $hashedpw ) )
    {
        fail_user_error("Invalid username/password");    # sad
    }

    # Username/password combination found and is valid.
    if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
        report_elapsed_time( "ensure_valid_device_and_user_for_uploading: done "
              . "user, now checking device" );
    }
    check_device_registered($device);
}

sub get_server_storedvar_text {
    my ($name) = @_;
    my $query  = "SELECT valueText FROM _server_storedvars WHERE name=?";
    my $sth    = $dbh->prepare($query);
    $sth->execute($name)
      or fail_server_error("Couldn't check _server_storedvars: $sth->errstr");
    my $result = $sth->fetchrow_array();    # only one row, only one column
    return $result;
}

sub get_server_storedvar_real {
    my ($name) = @_;
    my $query  = "SELECT valueReal FROM _server_storedvars WHERE name=?";
    my $sth    = $dbh->prepare($query);
    $sth->execute($name)
      or fail_server_error("Couldn't check _server_storedvars: $sth->errstr");
    my $result = $sth->fetchrow_array();    # only one row, only one column
    return $result;
}

sub server_storedvar_text_for_client {
    my ($var) = @_;
    my $val = get_server_storedvar_text($var);
    return "$var:$val\n";
}

sub server_storedvar_real_for_client {
    my ($var) = @_;
    my $val = get_server_storedvar_real($var);
    return "$var:$val\n";
}

sub name_value_pair_for_client {
    my ( $name, $value ) = @_;
    return "$name:$value\n";
}

sub unsupported_operation {
    my ($operation) = @_;
    fail_user_error("operation=$operation: not supported");
}

sub get_server_id_info {
    my $reply = "";
    $reply .= name_value_pair_for_client( "databaseTitle",  $db_title );
    $reply .= name_value_pair_for_client( "idPolicyUpload", $upload_policy );
    $reply .=
      name_value_pair_for_client( "idPolicyFinalize", $finalize_policy );
    $reply .= server_storedvar_real_for_client("serverCamcopsVersion");
    for ( my $i = 1 ; $i <= NUMBER_OF_IDNUMS ; $i++ ) {
        $reply .=
          name_value_pair_for_client( "idDescription" . $i, $iddesc[$i] );
        $reply .= name_value_pair_for_client( "idShortDescription" . $i,
            $idshortdesc[$i] );
    }
    return $reply;
}

#==============================================================================
# Main
#==============================================================================

if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
    report_elapsed_time("STARTING MAIN SECTION");
}

# Check appropriate input type
ensure_method_is_post();    # Will abort in case of failure

if ( $DEBUGLEVEL >= DEBUG_RIDICULOUS ) {

    # will be optimized away at other debug levels
    show_all_env_vars();
}
if ( $DEBUGLEVEL >= DEBUG_DANGER ) {
    show_all_post_vars();
}

my $operation = get_post_var("operation");

# Authentication variables (which ones we need depend on the operation)...
my $device = get_post_var("device");
if ( $operation eq "check_device_registered" ) {

    # Permitted without a valid username
    writelog( "Incoming connection from IP=$remote_addr, port=$remote_port, "
          . "device=$device, operation=$operation" );
    check_device_registered($device);
    succeed( "CamCOPS: check_device_registered", $operation );    # will exit
}
my $user     = get_post_var("user");
my $password = get_post_var("password");
writelog( "Incoming connection from IP=$remote_addr, port=$remote_port, "
      . "device=$device, user=$user, operation=$operation" );

# Choose an operation

#------------------------------------------------------------------------------
# Tablet access
#------------------------------------------------------------------------------
if ( $operation eq "check_upload_user_and_device" ) {
    ensure_valid_device_and_user_for_uploading( $user, $password, $device );
    succeed_generic($operation);
}
elsif ( $operation eq "start_upload" ) {
    start_device_upload_batch( $device, $user );
    succeed_generic($operation);
}
elsif ( $operation eq "end_upload" ) {
    my ( $batchtime, $preserving ) =
      get_device_upload_batch_details( $device, $user );

    # ensure it's the same user finishing as starting!
    end_device_upload_batch( $device, $user, $batchtime, $preserving );
    succeed_generic($operation);
}
elsif ( $operation eq "upload_table" ) {
    if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
        report_elapsed_time("upload_table - start; about to validate user");
    }
    ensure_valid_device_and_user_for_uploading( $user, $password, $device );
    if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
        report_elapsed_time("upload_table - about to process input");
    }
    my ( $batchtime, $preserving ) =
      get_device_upload_batch_details( $device, $user );

    # version
    my $camcops_version = get_post_var( "camcops_version", 0 );

    # table
    my $table = get_post_var("table");
    ensure_valid_table_name($table);

    # fields
    my @fields  = get_fields_from_post_var("fields");
    my $nfields = scalar(@fields);
    if ( $nfields < 1 ) {
        fail_user_error("nfields=$nfields: can't be less than 1");
    }
    my $clientpk_name = $fields[0];

    # records
    my $nrecords = get_post_var("nrecords");
    if ( $nrecords < 0 ) {
        fail_user_error("nrecords=$nrecords: can't be less than 0");
    }
    if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
        report_elapsed_time("upload_table - about to get PKs");
    }
    my @server_active_record_pks =
      get_server_pks_of_active_records( $table, $device );
    my @server_uploaded_pks;
    my %hash;    # We'll re-use the hash; its values are always the keys
    my $new_or_updated = 0;
    mark_table_dirty( $device, $table );
    for ( my $r = 0 ; $r < $nrecords ; $r++ ) {
        if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
            report_elapsed_time("upload_table - processing record");
        }
        my $recname = "record" . $r;
        my @values  = get_values_from_post_var($recname);
        my $nvalues = scalar(@values);
        if ( $nfields != $nvalues ) {

            #writelog("VALUES: @values\nFIELDS: @fields"); # debugging only
            fail_user_error( "Number of fields in field list ($nfields) "
                  . "doesn't match number of values in record "
                  . "$r ($nvalues)" );
        }
        @hash{@fields} = @values;

        # CORE: CALLS upload_record
        my ( $oldserverpk, $newserverpk ) = upload_record( $device, $table,
            $clientpk_name, \%hash, $r, $camcops_version );
        if ( defined $newserverpk ) {
            $new_or_updated++;
        }

        push( @server_uploaded_pks, $oldserverpk );
    }
    if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
        report_elapsed_time(
            "upload_table - about to deal with absent " . "records" );
    }

    # Now deal with any ABSENT (not in uploaded data set) conditions.
    my @server_pks_for_deletion =
      in_A_not_B( \@server_active_record_pks, \@server_uploaded_pks );
    flag_deleted( $device, $table, @server_pks_for_deletion );

    # Success
    if ( $DEBUGLEVEL >= DEBUG_EXTENDED ) {
        writelog( "server_active_record_pks: "
              . array_to_csv_except_undef( \@server_active_record_pks ) );
        writelog( "server_active_record_pks: "
              . array_to_csv_except_undef( \@server_active_record_pks ) );
        writelog( "server_uploaded_pks: "
              . array_to_csv_except_undef( \@server_uploaded_pks ) );
        writelog( "server_pks_for_deletion: "
              . array_to_csv_except_undef( \@server_pks_for_deletion ) );
        writelog( "Table $table, number of missing records (deleted): "
              . scalar(@server_pks_for_deletion) );
    }

    # Auditing occurs at commit_all.
    if ( $DEBUGLEVEL >= DEBUG_VERBOSE ) {
        report_elapsed_time("upload_table - done");
    }
    succeed(
        "CamCOPS: upload successful; $nrecords records uploaded to table "
          . "$table",
        "Table $table upload successful"
    );
}
elsif ( $operation eq "upload_record" ) {
    ensure_valid_device_and_user_for_uploading( $user, $password, $device );
    my ( $batchtime, $preserving ) =
      get_device_upload_batch_details( $device, $user );
    my $table           = get_post_var("table");
    my $clientpk_name   = get_post_var("pkname");
    my %hash            = get_fields_and_values( "fields", "values" );
    my $clientpk_value  = $hash{$clientpk_name};
    my $camcops_version = get_post_var( "camcops_version", 0 );
    my %wherehash       = ( $clientpk_name, $clientpk_value );

    # ... use () not {} and don't use the fat comma => here
    my @serverpks =
      get_server_pks_of_specified_records( $device, $table, \%wherehash );
    if ( scalar(@serverpks) == 0 ) {

        # Insert
        my $serverpk =
          insert_record( $device, $table, \%hash, undef, $camcops_version );

        #audit($user, $device, $table, $serverpk, "upload_record: insert");
        succeed( "CamCOPS: upload-insert", "UPLOAD-INSERT" );
    }
    else {
        # Update
        my $oldserverpk = $serverpks[0];
        my $newserverpk = duplicate_record( $device, $table, $oldserverpk );
        flag_modified( $device, $table, $oldserverpk, $newserverpk );
        update_new_copy_of_record( $table, $newserverpk, \%hash, $oldserverpk,
            $camcops_version );
        succeed( "CamCOPS: upload-update", "UPLOAD-UPDATE" );
    }

    # Auditing occurs at commit_all.
}
elsif ( $operation eq "upload_empty_tables" ) {
    ensure_valid_device_and_user_for_uploading( $user, $password, $device );
    my ( $batchtime, $preserving ) =
      get_device_upload_batch_details( $device, $user );
    my @tables = get_tables_from_post_var("tables");
    foreach my $table (@tables) {
        flag_all_records_deleted( $device, $table );

        #audit($user, $device, $table, undef, "upload_empty_tables");
    }
    succeed( "CamCOPS: upload_empty_tables", "UPLOAD-EMPTY-TABLES" );

    # Auditing occurs at commit_all.
}
elsif ( $operation eq "start_preservation" ) {
    ensure_valid_device_and_user_for_uploading( $user, $password, $device );
    my ( $batchtime, $preserving ) =
      get_device_upload_batch_details( $device, $user );
    start_preserving($device);

    # Auditing occurs at commit_all.
    #audit($user, $device, undef, undef, "start_preservation");
    succeed( "CamCOPS: start_preservation successful", "STARTPRESERVATION" );
}
elsif ( $operation eq "delete_where_key_not" ) {
    ensure_valid_device_and_user_for_uploading( $user, $password, $device );
    my $table = get_post_var("table");
    my ( $batchtime, $preserving ) =
      get_device_upload_batch_details( $device, $user );
    my $clientpk_name   = get_single_field_from_post_var("pkname");
    my @clientpk_values = get_values_from_post_var("pkvalues");
    flag_deleted_where_clientpk_not( $device, $table, $clientpk_name,
        @clientpk_values );

    # Auditing occurs at commit_all.
    succeed( "CamCOPS: delete_where_key_not successful; table $table trimmed",
        "Trimmed" );
}
elsif ( $operation eq "which_keys_to_send" ) {
    ensure_valid_device_and_user_for_uploading( $user, $password, $device );
    my $table = get_post_var("table");
    my ( $batchtime, $preserving ) =
      get_device_upload_batch_details( $device, $user );
    my $clientpk_name   = get_single_field_from_post_var("pkname");
    my @clientpk_values = get_values_from_post_var( "pkvalues", 0 );
    my $npkvalues       = scalar(@clientpk_values);
    my @client_dates    = get_values_from_post_var( "datevalues", 0 );
    my $ndatevalues     = scalar(@client_dates);

    if ( $npkvalues != $ndatevalues ) {
        fail_user_error( "Number of PK values ($npkvalues) doesn't match "
              . "number of dates ($ndatevalues)" );
    }

    # 1. The client sends us all its PKs. So "delete" anything not in that list.
    flag_deleted_where_clientpk_not( $device, $table, $clientpk_name,
        @clientpk_values );

    # 2. See which ones are new or updates.
    my @pks_needed;
    for ( my $i = 0 ; $i < $npkvalues ; $i++ ) {
        my $clientpkval       = $clientpk_values[$i];
        my $client_date_value = $client_dates[$i];
        my ( $found, $serverpk ) =
          record_exists( $device, $table, $clientpk_name, $clientpkval );
        if ( !$found
            || !record_identical_by_date( $table, $serverpk,
                $client_date_value ) )
        {
            push( @pks_needed, $clientpkval );
        }
    }

    # Success
    succeed( "CamCOPS: which_keys_to_send successful: table $table",
        array_to_csv_except_undef( \@pks_needed ) );
}
elsif ( $operation eq "register" ) {
    ensure_valid_user_for_device_registration( $user, $password );
    my $device_friendly_name = get_post_var( "devicefriendlyname", 0 );
    my $camcops_version      = get_post_var( "camcops_version",    0 );
    my $secdevpk = register_device( $device, $user, $device_friendly_name,
        $camcops_version );
    audit( $user, $device, "_security_devices", $device,
        "register, friendly_name=$device_friendly_name" );
    my $reply = "Registered\n";
    $reply .= get_server_id_info();
    succeed( "CamCOPS: registration successful for device $device", $reply );
}
elsif ( $operation eq "get_id_info" ) {
    ensure_valid_device_and_user_for_uploading( $user, $password, $device );
    my $reply = get_server_id_info();
    succeed( "CamCOPS: get_id_info", $reply );
}

#------------------------------------------------------------------------------
# Mobile Web (may be disabled by config)
#------------------------------------------------------------------------------
if ( !$allow_mobileweb ) {
    unsupported_operation($operation);    # will exit
}

if ( $operation eq "count" ) {
    ensure_valid_user_for_webstorage( $device, $user, $password );
    my $table = get_post_var("table");
    my %wherehash = get_fields_and_values( "wherefields", "wherevalues", 0 );
    my %wherenothash =
      get_fields_and_values( "wherenotfields", "wherenotvalues", 0 );
    my $count = count_records( $device, $table, \%wherehash, \%wherenothash );
    succeed( "CamCOPS: COUNT", $count );
}
elsif ( $operation eq "select" ) {

    # Establish parameters
    ensure_valid_user_for_webstorage( $device, $user, $password );
    my $table = get_post_var("table");
    my %wherehash = get_fields_and_values( "wherefields", "wherevalues", 0 );
    my %wherenothash =
      get_fields_and_values( "wherenotfields", "wherenotvalues", 0 );
    my @fields = get_fields_from_post_var("fields");

    # Select records
    my ( $nrecords, @values ) =
      select_records_with_specified_fields( $device, $table, \%wherehash,
        \%wherenothash, @fields );

    # Send results back to user
    my $nfields = scalar(@fields);
    my $fieldlist = join( ",", @fields );

    # .... even though this probably reinvents what the client sent us!
    my $reply    = "nrecords:$nrecords\nnfields:$nfields\nfields:$fieldlist";
    my $valuenum = 0;
    for ( my $rec = 0 ; $rec < $nrecords ; $rec++ ) {
        my @encodedvalues;
        for ( my $f = 0 ; $f < $nfields ; $f++ ) {
            push( @encodedvalues, encode_single_value( $values[$valuenum] ) );
            ++$valuenum;
        }
        $reply .= "\nrecord$rec:" . join( ",", @encodedvalues );
    }
    my $nwheres    = keys %wherehash;
    my $nwherenots = keys %wherenothash;
    my $auditstring =
        "webclient SELECT "
      . join( ",", @fields )
      . " FROM $table "
      . "WHERE "
      . where_clause_for_audit( \%wherehash );
    if ( $nwheres > 0 && $nwherenots > 0 ) {
        $auditstring .= " AND ";
    }
    $auditstring .= where_not_clause_for_audit( \%wherenothash );
    audit( $user, $device, $table, undef, $auditstring );
    succeed( "CamCOPS: SELECT", $reply );
}
elsif ( $operation eq "insert" ) {

    # Non-transactional
    # *** should probably pay special attention to "id" field, ensuring it
    # remains unique per device/table where _current.
    ensure_valid_user_for_webstorage( $device, $user, $password );
    my $table           = get_post_var("table");
    my $clientpk_name   = get_post_var("pkname");
    my $camcops_version = get_post_var( "camcops_version", 0 );
    my $max_client_pk   = get_max_client_pk( $device, $table, $clientpk_name );
    if ( !defined($max_client_pk) ) {
        $max_client_pk = 0;
    }
    my $clientpk_value = $max_client_pk + 1;
    my %hash = get_fields_and_values( "fields", "values" );
    $hash{$clientpk_name} = $clientpk_value;
    my $server_pk =
      insert_record( $device, $table, \%hash, undef, $camcops_version );
    commit_table( $device, $user, $now_dt_utc, 0, $table, 1 );
    audit( $user, $device, $table, $server_pk, "webclient INSERT" );
    succeed( "CamCOPS: INSERT", $clientpk_value );
}
elsif ( $operation eq "update" ) {

    # Non-transactional
    ensure_valid_user_for_webstorage( $device, $user, $password );
    my $batchtime       = $now_dt_utc;
    my $table           = get_post_var("table");
    my $camcops_version = get_post_var( "camcops_version", 0 );
    my %hash            = get_fields_and_values( "fields", "values" );
    my %wherehash = get_fields_and_values( "wherefields", "wherevalues", 0 );
    my @serverpks =
      get_server_pks_of_specified_records( $device, $table, \%wherehash );

    if ( scalar(@serverpks) == 0 ) {
        fail_user_error( "No records found to UPDATE (table=$table, where "
              . Dumper(%wherehash)
              . ")" );
    }

    # The UPDATE information might not include the date; so we assume that a
    # real change is being made.
    foreach my $serverpk (@serverpks) {
        my $newserverpk = duplicate_record( $device, $table, $serverpk );
        flag_modified( $device, $table, $serverpk, $newserverpk );
        update_new_copy_of_record( $table, $newserverpk, \%hash, $serverpk,
            $camcops_version );
        audit( $user, $device, $table, $serverpk,
            "webclient UPDATE: old record deactivated" );
        audit( $user, $device, $table, $newserverpk,
            "webclient UPDATE: new record inserted" );
    }
    commit_table( $device, $user, $now_dt_utc, 0, $table, 1 );
    succeed( "CamCOPS: UPDATE", "Updated" );
}
elsif ( $operation eq "delete" ) {

    # Non-transactional
    ensure_valid_user_for_webstorage( $device, $user, $password );
    my $table = get_post_var("table");
    my %wherehash = get_fields_and_values( "wherefields", "wherevalues", 0 );
    webclient_delete_records( $device, $user, $table, \%wherehash );

    # ... doesn't need a separate commit_table
    audit( $user, $device, $table, undef,
        "webclient DELETE WHERE " . where_clause_for_audit( \%wherehash ) );
    succeed( "CamCOPS: DELETE", "Deleted" );
}

#------------------------------------------------------------------------------
# Unrecognized operation.
#------------------------------------------------------------------------------

unsupported_operation($operation);
