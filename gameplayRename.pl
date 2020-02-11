#!/usr/bin/perl

# changes files ending with .mp4 to my filename format, e.g. XRebirth.Gameplay,part.32.mp4

use strict;

my $tdir = './';
my $dir;
my $entry;
my $newentry;

if ($#ARGV < 1)
{
	print "Usage: gameplayRename.pl <startFromNumber> [name_prefix]";
	exit(1);
}

my $i = int(shift);
my $name = join(' ',@ARGV);
my @entries;


if( opendir($dir,$tdir) )
{
	while( $entry = readdir($dir) )
	{
		if( $entry =~ m/\.mp4$/ && $entry !~ m/^\./ && $entry ne 'rename.pl' )
		{
			push(@entries,$entry);
		}
	}

	closedir($dir);

	@entries = sort(@entries);
	foreach my $entry (@entries)
	{
		$newentry = $name.$i.'.mp4';
		++$i;
		$newentry =~ s/\[HD-bits\.ro\]//i;
		$newentry =~ s/%5BHD-bits\.ro%5D\.?//i;
		$newentry =~ s/\[HDbits\.ro\]//i;
		$newentry =~ s/[\[\]!#@%\$\^&\*\(\)']//g;
		$newentry =~ s/  / /g;
		$newentry =~ s/ /./g;
		$entry = $tdir.'/'.$entry;
		$newentry = $tdir.'/'.$newentry;
		print "$entry -> $newentry\n";
		rename($entry,$newentry);
	}
}


