#!/usr/bin/perl

# Removes: HD-bits.ro] from all files name in the directory

use strict;

my $tdir = './';
my $dir;
my $entry;
my $newentry;

if( opendir($dir,$tdir) )
{
	while( $entry = readdir($dir) )
	{
		if( $entry !~ m/^\./ && $entry ne 'rename.pl' )
		{
			$newentry = $entry;
			$newentry =~ s/\[HD-bits\.ro\]//i;
			$newentry =~ s/%5BHD-bits\.ro%5D\.?//i;
			$newentry =~ s/\[HDbits\.ro\]//i;
			$newentry =~ s/[\[\]!#@%\$\^&\*\(\)']//g;
			$newentry =~ s/  / /g;
			$newentry =~ s/ /./g;
#			$newentry =~ m/S\d\d.E\d\d/;
#			my $sep = $&;
#			$sep =~ s/\.//;
#			print "$sep\n";
#			$newentry =~ s/S\d\d.E\d\d/$sep/;
			$entry = $tdir.'/'.$entry;
			$newentry = $tdir.'/'.$newentry;
			rename($entry,$newentry);
		}
	}

	closedir($dir);
}


