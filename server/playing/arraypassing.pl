#!/usr/bin/perl -w

use Data::Dumper;

sub mysub
{
    my @array = @_;
    print "IN FUNCTION\n";
    print "array: @array\n";
}

my @arr = (1,2,3);

print "As array\n";
mysub(@arr);

print "As three elements\n";
mysub(4,5,6);


