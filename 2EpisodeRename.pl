#!/usr/bin/perl

# Removes characters needing escaping from all files name in the directory and renames to an episode short name

use strict;
use Getopt::Long;

my $tdir = './';
my $dir;
my $entry;
my $newentry;

my $rename_confirmed = 0;
my $season = '';
my $postfix = '';
GetOptions ('yes' => \$rename_confirmed, 'season:s' => \$season, 'postfix:s' => \$postfix);

if( opendir($dir,$tdir) )
{
	while( $entry = readdir($dir) )
	{
		if( $entry =~ m/\.(mkv|avi)$/ && $entry !~ m/^\./ && $entry ne 'rename.pl' )
		{
			$newentry = $entry;
			$newentry =~ s/[\[\]!#@%\$\^&\*\(\)]//g;
			$newentry =~ s/  / /g;
			$newentry =~ s/ /./g;
			$newentry = rename2Episode($newentry);
			$entry = $tdir.'/'.$entry;
			$newentry = $tdir.'/'.$newentry;
			if ($rename_confirmed)
			{
				rename($entry,$newentry);
			}
			else
			{
				print "$entry -> $newentry\n";
			}

		}
	}

	closedir($dir);
}

sub rename2Episode
{
	$_ = shift;
	m/\.[a-zA-Z0-9]{3,4}$/;
	my $extension = $&;
	m/s[0-9]{2}e[0-9]{2}(-[0-9]{2})?/i;
	my $seasonEp = $&;
	if (length($seasonEp) != 6)
	{
		if (m/[0-9]{1}x[0-9]{2}(-[0-9]{2})?/i)
		{
			$seasonEp = $&;
			$seasonEp =~ s/[0-9]{1}x/E/i;
		}
		elsif (m/title_t[0-9]{2}/i)
        {
			$seasonEp = $&;
			$seasonEp =~ s/title_t//i;
            my $si = int($seasonEp) + 1;
            $seasonEp = "E".sprintf("%02d", $si);
        }
		elsif (m/\.[0-9]{1,2}[0-9]{2}\./i)
		{
			$seasonEp = $&;
			$seasonEp =~ s/\.//g;
			if (length($seasonEp) > 3)
			{
				$seasonEp =~ s/[0-9]{1,2}/E/i;
			}
			else
			{
				$seasonEp =~ s/[0-9]{1}/E/i;
			}
#			print "$seasonEp\n";
		}
        elsif (m/[1-9][0-9]{2}/i)
        {
            $seasonEp = $&;
			$seasonEp =~ s/^[1-9]/E/i;
        }
	}
	else
	{
		$seasonEp =~ s/s[0-9]{2}e/E/i;
	}

	$season.$seasonEp.$postfix.$extension;
}
