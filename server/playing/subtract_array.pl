#!/usr/bin/perl -w

use strict;
use warnings;
use Data::Dumper;
#use Acme::Tools qw(minus);
use Time::HiRes;

sub array_to_csv_except_undef
{
    my ($arrayref) = @_;
    return join(",", grep(defined, @$arrayref));
}

sub in_A_not_B_1
{
    # call as in_A_not_B(\@A, \@B)
    my ($refA, $refB) = @_;
    my %seen; # empty hash
    @seen{@$refA} = (); # inserts A values as keys, with undef values
    delete @seen{@$refB}; # removes keys that are B values
    return keys %seen;
    # http://my.safaribooksonline.com/book/programming/perl/1565922433/arrays/ch04-29725
}

sub in_A_not_B_4
{
    # call as in_A_not_B(\@A, \@B)
    my ($refA, $refB) = @_;
    # Create a hash representing B
    my %seen; # empty hash
    $seen{$_} = undef foreach (@$refB);
    # grep only leaves what evaluates to true.
    # if an element of A is not in B, it is
    # left in place
    return grep { not exists $seen{$_} } @$refA;
    # http://www.perlmonks.org/?node_id=205991
}

sub in_A_not_B_3
{
    # call as in_A_not_B(\@A, \@B)
    my ($refA, $refB) = @_;
    my %seen; # empty hash
    @seen{@$refA} = (); # inserts A values as keys, with undef values
    for (@$refB)
    {
        delete $seen{$_} if exists $seen{$_}; # removes keys that are B values
    }
    return keys %seen;
    # http://my.safaribooksonline.com/book/programming/perl/1565922433/arrays/ch04-29725
}

sub in_A_not_B_2
{
    my ($refA, $refB) = @_;
    my %in_b = map {$_ => 1} @$b;
    my @diff  = grep {not $in_b{$_}} @$a;
    return @diff;
}


#sub in_A_not_B_with_C_paired_to_A
#{
#    my ($refA, $refB, $refC, $refAtrimmed, $refCtrimmed) = @_;
#    my %seen;
#    @seen{@$refA} = @$refC;
#    delete @seen{@$refB};
#    @$refAtrimmed = keys %seen; # written back
#    @$refCtrimmed = values %seen; # written back
#}

#sub in_C_where_A_not_in_B
#{
#    my ($refA, $refB, $refC, $refCtrimmed) = @_;
#    my %seen;
#    @seen{@$refA} = @$refC;
#    delete @seen{@$refB};
#    @$refCtrimmed = values %seen; # written back
#}


my @a = qw(green yellow purple blue pink);
my @b = qw(red green blue);

my @c = (1, 2, 3, 4, 5);
#my @c = undef;
#my @d = (3, 4);
#my @d;
my @d = undef;
my @e = (undef, 1, undef, 2, undef, 3, undef);

print "------------- 1 \n";
print Dumper [ in_A_not_B_1(\@a, \@b) ];
print Dumper [ in_A_not_B_1(\@c, \@d) ];
print "------------- 2 \n";
print Dumper [ in_A_not_B_2(\@a, \@b) ];
print Dumper [ in_A_not_B_2(\@c, \@d) ];
print "------------- 3 \n";
print Dumper [ in_A_not_B_3(\@a, \@b) ];
print Dumper [ in_A_not_B_3(\@c, \@d) ];
print "------------- 4 \n";
print Dumper [ in_A_not_B_4(\@a, \@b) ];
print Dumper [ in_A_not_B_4(\@c, \@d) ];

#print Dumper [ minus(\@a, \@b) ];

print array_to_csv_except_undef(\@e), "\n";

my @onearray = ();
print "onearray last index: $#onearray \n";
print "first line $onearray[0]\n" if ($#onearray >= 0);
foreach ( @onearray[1 .. $#onearray] )
{
    print "2-end loop $_\n";
}

print "time: " . Time::HiRes::time() . "\n";
