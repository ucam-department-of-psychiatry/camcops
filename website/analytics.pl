#!/usr/bin/perl -w

=pod
    Author: Rudolf Cardinal (rudolf@pobox.com)
    Copyright (C) 2012, 2013 Rudolf Cardinal, University of Cambridge, Wellcome Trust

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
# TABLES REQUIRED (not executed here; do it yourself):
#==============================================================================

=for comment
CREATE DATABASE camcops_analytics DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
USE camcops_analytics;
CREATE TABLE IF NOT EXISTS contacts (
    pk INTEGER NOT NULL AUTO_INCREMENT,
    analytics_server_datetime TEXT,
    source_type INTEGER,                # 0 unknown, 1 server, 2 app
    client_ip TEXT,
    client_datetime TEXT,
    camcops_version DOUBLE,

    device TEXT,                        # for app
    camcops_server TEXT,                # for app
    db_version INTEGER,                 # for app
    use_clinical INTEGER,               # for app
    use_educational INTEGER,            # for app
    use_research INTEGER,               # for app
    use_commercial INTEGER,             # for app

    PRIMARY KEY(pk)
);
CREATE TABLE IF NOT EXISTS nrecords (
    pk INTEGER NOT NULL AUTO_INCREMENT,
    contacts_pk INTEGER,
    table_name TEXT,
    nrecords INTEGER,

    PRIMARY KEY(pk)
);

=cut

#==============================================================================
# Includes
#==============================================================================

#use diagnostics;
use strict;
use warnings;

use Apache::DBI;
# ... persistent database connections; see
#     http://perl.apache.org/docs/1.0/guide/databases.html
# ... install with: sudo aptitude install libapache-dbi-perl
$Apache::DBI::DEBUG = 0;
# ... level 2 shows passwords for reconnect; level 1 shows passwords for
#     connect; avoid
use CGI;
use DateTime;    # sudo apt-get install libdatetime-perl
use DBI;    # sudo apt-get install libdbi-perl
use MIME::Base64;
use Text::CSV;    # sudo apt-get install libtext-csv-perl

#==============================================================================
# for mod_perl
#==============================================================================
# see database.pl
no warnings qw(redefine);

#==============================================================================
# Database globals (forward referencing with &)
#==============================================================================

# Connect to database
our ( $dsn, $dbname, $dbuser, $dbpassword ) = &get_db_vars();
our $dbh = DBI->connect(
    $dsn, $dbuser,
    $dbpassword,
    {
        #PrintError => 1,  # report errors via warn()?
        #RaiseError => 0 # report errors via die()?
        ShowErrorStatement => 1,   # adds the offending SQL to the error message
        HandleError =>
          \&dbi_error_handler      # provide a custom function to handle errors
    }
) || fail_server_error("Couldn't connect to database: $DBI::errstr");
$dbh->{AutoCommit} = 0;            # enable transactions, if possible

#==============================================================================
# Database globals and error handling (forward referencing with &)
#==============================================================================

sub dbi_error_handler {
    my ( $message, $handle, $first_value ) = @_;
    fail_server_error("Database error: $message");
}

#==============================================================================
# Date
#==============================================================================

sub time_to_string {
    my $dt      = shift;
    my $mainbit = $dt->strftime("%Y-%m-%dT%H:%M:%S.%3N");
    my $tz      = $dt->strftime("%z");                      # e.g. "+0000"
    my $tz2 =
        substr( $tz, 0, 3 ) . ":"
      . substr( $tz, 3, 2 );    # convert "+0000" to "+00:00"
    return $mainbit . $tz2;

  # YYYY-MM-DDTHH:mm:ss.SSSZ, e.g. 2012-07-25T16:38:02.257+01:00
  # RFC822-conformant dates (using "%a, %d %b %Y %H:%M:%S %z").
  # http://search.cpan.org/~drolsky/DateTime-0.76/lib/DateTime.pm#Format_Modules
}

sub get_local_time_as_string {
    return time_to_string( DateTime->now( time_zone => 'local' ) );
}

#sub get_utc_time_as_string
#{
#    return time_to_string( DateTime->now );
#}

our $now = get_local_time_as_string();    # Global

#==============================================================================
# Environment variables
#==============================================================================

sub get_env_var_or_fail {
    my ($var) = @_;
    my $val = $ENV{$var};
    unless ($val) {
        fail_server_error(
            "Web server configuration wrong - environment variable $var not set"
        );
    }
    return $val;
}

sub show_all_env_vars {

    # Minimal output; call this on its own.
    foreach my $var ( sort( keys(%ENV) ) ) {
        unless ( $var eq "DB_PASSWORD" )    # Security risk otherwise!
        {
            my $val = $ENV{$var};
            $val =~ s/\n/\\n/g;
            $val =~ s/"/\\"/g;
            writelog("${var}=\"${val}\"");
        }
    }
}

sub get_db_vars() {
    my $db_name     = get_env_var_or_fail("DB_NAME");
    my $db_user     = get_env_var_or_fail("DB_USER");
    my $db_password = get_env_var_or_fail("DB_PASSWORD");

    # The next line assumes the use of MySQL.
    return (
        "DBI:mysql:" . $db_name . ";mysql_enable_utf8=1",    # DSN
        $db_name,
        $db_user,
        $db_password
    );
}

#==============================================================================
# Logging, exiting
#==============================================================================

our @logmessages = ();                                       # Global

sub writelog {
    push( @logmessages, @_ ) if (@_);
}

sub send_log {
    foreach (@logmessages) {
        print("$_\n");
    }
}

sub send_log_stderr {
    foreach (@logmessages) {
        print( STDERR "$_\n" );
    }
}

sub finish {

    # Header, with a status code, content type, and two newlines at the end.
    my ( $status, $reply ) = @_;
    writelog(
        "CamCOPS analytics script finishing at " . get_local_time_as_string() );
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
    finish( "200 OK", $reply );

    # For debugging:
    send_log_stderr();    # so it also appears in the HTTPD log
    $dbh->commit;
    exit 0;
}

sub fail_user_error {
    writelog( "CLIENT-SIDE SCRIPT ERROR", @_ );
    finish("400 Bad Request: @_");

    # For debugging:
    send_log_stderr();    # so it also appears in the HTTPD log
    $dbh->commit;
    exit 0;
}

sub fail_server_error {
    writelog( "SERVER-SIDE SCRIPT ERROR", @_ );
    finish("503 Database Unavailable: @_");
    send_log_stderr();    # so it also appears in the HTTPD log
    $dbh->rollback;
    exit 1;
}

sub fail_prepare_error {
    fail_server_error("Statement preparation error: @_");
}

sub fail_execute_error {
    fail_server_error("Statement execution error: @_");
}

#==============================================================================
# CGI input functions
#==============================================================================

our $cq = CGI->new;    # CGI query

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

sub get_post_var_or_fail {
    my ($var) = @_;
    my $val = $cq->param($var);
    unless ($val) {
        fail_user_error("ERROR: Must provide the variable: $var");
    }
    return $val;
}

sub get_post_var_or_undef {
    my ($var) = @_;
    return $cq->param($var);
}

#==============================================================================
# Conversion to/from quoted SQL values
#==============================================================================

our $csv = Text::CSV->new(
    { # http://search.cpan.org/~makamaka/Text-CSV-1.21/lib/Text/CSV.pm#is_quoted
        escape_char         => "'",
        quote_char          => "'",
        binary              => 1,     # REQUIRED for embedded newlines
        blank_is_undef      => 1,
        allow_loose_escapes => 1,

        # verbatim => 1,
        quote_space => 0
    }
) or fail_server_error( "Can't use Text::CSV: " . Text::CSV->error_diag() );

# Embedded newlines: see http://search.cpan.org/~makamaka/Text-CSV-1.21/lib/Text/CSV.pm#parse

sub decode_single_value {
    my ($v) = @_;

    #writelog("incoming value: $v"); # debugging only
    if (   !defined($v)
        || $v =~ /^NULL$/i
        || length($v) == 0 )
    {
	# ... case-insensitive match

	#writelog("NULL found"); # debugging only

	# NULL: replace with a code indicating a proper NULL (or we'll insert
	# the string "NULL")
        $v = undef;
    }
    elsif (
        $v =~ m/
	    ^X'                       (?# begins with X')
	    ([a-fA-F0-9][a-fA-F0-9])+ (?# one or more hex pairs)
	    '$                        (?# ends with ')
	/x
      )
    {
	# ... the x allows whitespace/comments in the regex

	#writelog("BLOB FOUND: hex encoding"); # debugging only
	# SPECIAL HANDLING for BLOBs: a string like X'01FF' means a hex-encoded
	# BLOB... because Titanium is rubbish at blobs, so we encode them as
	# special string literals.
	# Hex-encoded BLOB, like X'CDE7A24B1A9DBA3148BCB7A0B9DA5BB6A424486C'
        $v = substr( $v, 2, length($v) - 3 );    # strip off the start and end
        $v =~ s/([a-fA-F0-9][a-fA-F0-9])/chr(hex($1))/eg;

	# or pack: http://stackoverflow.com/questions/2427527
	# Perl strings can contain zero/null bytes:
	# 	http://docstore.mik.ua/orelly/perl/cookbook/ch01_01.htm
	# BLOBs to/from to the database:
	# 	http://www.james.rcpt.to/programs/mysql/blob/
    }
    elsif (
        $v =~ m{
	    ^64'
	    (?: [A-Za-z0-9+/]{4} )*                   (?# zero or more quads, followed by)
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
        $v = substr( $v, 3, length($v) - 4 );    # strip off the start and end
	#writelog("STRIPPED BLOBSTRING: LEFT: " . substr($v, 0, 10));
	#writelog("STRIPPED BLOBSTRING: RIGHT: " . substr($v, -10));
        $v = decode_base64($v);

        #writelog("BLOB: LEFT: " . substr($v, 0, 10));
        #writelog("BLOB: RIGHT: " . substr($v, -10));
    }

    # Strings are handled by Text::CSV and its escape/quote characters.
    # Numbers are handled automatically by Perl.
    #writelog("value: $v"); # debugging only
    return $v;
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
    foreach my $v (@values)    # modifying $v modifies the array
    {
        $v = decode_single_value($v);
    }

    # Re binding, see http://docstore.mik.ua/orelly/linux/dbi/ch05_03.htm
    return @values;
}

sub get_values_from_post_var_allowing_absence {
    my ($postvar) = @_;
    my $recvalues = get_post_var_or_undef($postvar);

    #writelog("record $r: $recvalues"); # debugging only
    my @values;
    if ( defined $recvalues ) {
        @values = decode_values($recvalues);
    }
    return @values;
}

#==============================================================================
# CamCOPS analytics table functions
#==============================================================================

sub insert_contact {
    my (
        $source_type,     $client_ip,    $client_now,
        $camcops_version, $device,       $camcops_server,
        $db_version,      $use_clinical, $use_educational,
        $use_research,    $use_commercial
    ) = @_;
    my $query = "
	INSERT INTO contacts (
	    analytics_server_datetime,
	    source_type, client_ip, client_datetime,
	    camcops_version,
	    device, camcops_server, db_version,
	    use_clinical, use_educational, use_research, use_commercial
	) VALUES (
	    ?,
	    ?,?,?,
	    ?,
	    ?,?,?,
	    ?,?,?,?
	)";
    my $sth = $dbh->prepare($query);
    $sth->execute(
        $now,             $source_type,     $client_ip,
        $client_now,      $camcops_version, $device,
        $camcops_server,  $db_version,      $use_clinical,
        $use_educational, $use_research,    $use_commercial
    );
    return $sth->{'mysql_insertid'};    # MySQL-specific
}

sub insert_count {
    my ( $contacts_pk, $table_name, $record_count ) = @_;
    my $query =
"INSERT INTO nrecords (contacts_pk, table_name, nrecords) VALUES (?, ?, ?)";
    my $sth = $dbh->prepare($query);
    $sth->execute( $contacts_pk, $table_name, $record_count );
}

#==============================================================================
# Main
#==============================================================================

writelog("CamCOPS analytics script starting at $now");
ensure_method_is_post();    # Will abort in case of failure

#show_all_env_vars(); # Debugging only
#show_all_post_vars(); # Debugging only
my $client_ip   = get_env_var_or_fail("REMOTE_ADDR");
my $remote_port = get_env_var_or_fail("REMOTE_PORT");
my $source_text = get_post_var_or_fail("source");       # "app" or "server"
my $source_type = 0;
if ( $source_text eq "server" ) {
    $source_type = 1;
}
elsif ( $source_text eq "app" ) {
    $source_type = 2;
}

my $device          = get_post_var_or_undef("device");
my $client_now      = get_post_var_or_undef("now");
my $camcops_version = get_post_var_or_undef("camcops_version");

my $camcops_server  = get_post_var_or_undef("server");
my $db_version      = get_post_var_or_undef("db_version");
my $use_clinical    = get_post_var_or_undef("use_clinical");
my $use_educational = get_post_var_or_undef("use_educational");
my $use_research    = get_post_var_or_undef("use_research");
my $use_commercial  = get_post_var_or_undef("use_commercial");

my @table_names   = get_values_from_post_var_allowing_absence("table_names");
my $ntables       = scalar(@table_names);
my @record_counts = get_values_from_post_var_allowing_absence("record_counts");
my $nrecordcounts = scalar(@record_counts);

writelog(
"Incoming connection from IP=$client_ip, port=$remote_port, source=$source_text, device=$device"
);

my $contacts_pk = insert_contact(
    $source_type,     $client_ip,      $client_now, $camcops_version,
    $device,          $camcops_server, $db_version, $use_clinical,
    $use_educational, $use_research,   $use_commercial
);
if ( $ntables != $nrecordcounts ) {
    fail_user_error(
"Number of tables ($ntables) doesn't match number of record counts ($nrecordcounts)"
    );
}
for ( my $t = 0 ; $t < $ntables ; $t++ ) {
    insert_count( $contacts_pk, $table_names[$t], $record_counts[$t] );
}

succeed("CamCOPS analytics recorded");
