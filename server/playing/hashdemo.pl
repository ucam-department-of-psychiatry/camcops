#!/usr/bin/perl -w

use strict;
use warnings;

sub in_A_not_B
{
    # call as in_A_not_B(\@A, \@B)
    my ($refA, $refB) = @_;
    my %seen; # empty hash
    @seen{@$refA} = (); # inserts A values as keys, with undef values
    delete @seen{@$refB}; # removes keys that are B values
    return keys %seen;
    # http://my.safaribooksonline.com/book/programming/perl/1565922433/arrays/ch04-29725
}

my @A = (1,2,3,4);
my @B = (2,3);
my @C;

print "A: @A \n";
print "B: @B \n";
print "C: @C \n";

my @a_not_b = in_A_not_B(\@A, \@B);
my @a_not_c = in_A_not_B(\@A, \@C);
my @c_not_a = in_A_not_B(\@C, \@A);
print "in A not B: @a_not_b \n";
print "in A not C: @a_not_c \n";
print "in C not A: @c_not_a \n";


