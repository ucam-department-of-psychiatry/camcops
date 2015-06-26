#!/usr/bin/perl -w

# Can use this with temporary environment varibles, e.g.:
#	DB_NAME=camcops DB_USER=root DB_PASSWORD=xxx ./fetchpng

#==============================================================================
# Standard includes
#==============================================================================

use strict;
use warnings;

use DBI;

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

sub save_png
{
    my ($filename, $data) = @_;
    open(my $out, ">:raw", $filename) or fail("Unable to open $filename");
    print $out $data;
    close($out);
}

sub save_pngs_from_task
{
    my ($table, $blobidfield, $filenameprefix) = @_;
    my $sql = "
        SELECT theblob, blobs.id, T.id
        FROM blobs
        INNER JOIN $table T
            ON blobs._device = T._device
            AND blobs.id = T.$blobidfield
        WHERE T._current
            AND blobs._current
    ";
    my $sth = $dbh->prepare($sql);
    $sth->execute();
    my $index = 0;
    while (my @rowarray = $sth->fetchrow_array())
    {
        my $filename = $filenameprefix . $index . ".png";
        my $blob_id = $rowarray[1];
        my $t_id = $rowarray[2];
        print("From $table ID $t_id, saving blob ID $blob_id as $filename\n");
        save_png($filename, $rowarray[0]);
        ++$index;
    }
}

sub save_png_by_server_pk
{
    my ($serverpk, $filename) = @_;
    my $sql = "SELECT theblob FROM blobs WHERE _pk = ?";
    my $sth = $dbh->prepare($sql);
    $sth->execute($serverpk);
    my $blob = $sth->fetchrow_array(); # only one row/column
    save_png($filename, $blob);
}

#==============================================================================
# Main
#==============================================================================

#save_pngs_from_task("moca", "trailpicture_blobid", "mocapic_");
save_png_by_server_pk(1, "spk1.png");
save_png_by_server_pk(2, "spk2.png");
