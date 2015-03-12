#!/usr/bin/perl -w

use Data::Dumper;

sub mysub
{
    my ($scalarref, $arrayref, $hashref) = @_;
    my $scalar = $$scalarref; # or ${$scalarref}
    my @array = @$arrayref; # or @{$arrayref}
    my %hash = %$hashref; # or %{$hashref}
    my $index = 0;
    my $key = "key4";
    print "IN FUNCTION\n";
    print "dereferenced scalar: $$scalarref\n";
    print "dereferenced array: @$arrayref\n";
    print "array[index] using double string: " . $$arrayref[$index] . "\n";
    print "array[index] using block: " . ${$arrayref}[$index] . "\n";
    print "array[index] using intermediate: " . $array[$index] . "\n";
    print "array[index] using arrow: " . $arrayref->[$index] . "\n";
    print "hash(key) using double string: " . $$hashref{$key} . "\n";
    print "hash(key) using block: " . ${$hashref}{$key} . "\n";
    print "hash(key) using intermediate: " . $hash{$key} . "\n";
    print "hash(key) using arrow: " . $hashref->{$key} . "\n";
}

my $scalar = 42;
my @array = (1, 2, 3); # not square brackets!
my %hash = ("key1", "value1", "key2", "value2", "key3", "value3");
$hash{"key4"} = "value4";

print "scalar: $scalar\n";
print "array: @array\n";
print "array[0]: $array[0]\n";
print "hash: " . Dumper(%hash) . "\n";
print "hash key1: " . $hash{"key1"} . "\n";

mysub(\$scalar, \@array, \%hash);

