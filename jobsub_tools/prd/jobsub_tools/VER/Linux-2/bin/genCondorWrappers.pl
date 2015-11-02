#!/usr/bin/perl 
use File::Basename;

$condor_dir = $ENV{LOCAL_CONDOR};

chomp(@cmds=`ls $condor_dir/condor*`);

foreach $exec(@cmds) {
  my $cmd = basename($exec);
  print "opening file $cmd to wrap to command $exec\n";

  open WRAP, ">$cmd" or die $!;
  print WRAP "#!/bin/sh\n\n";
  print WRAP "subhost=\$MINERVA_SUBMIT_HOST\n";
  print WRAP "if [ -z \"\$subhost\" ]; then\n";
  print WRAP "  subhost=\"gpsn01.fnal.gov\"\n";
  print WRAP "fi\n\n";
  print WRAP "#if we are on the submit host, then execute directly\n";
  print WRAP "#otherwise, execute from the submit host\n";
  print WRAP "if [ \"`hostname`\" = \"\$subhost\" ]; then\n";
  print WRAP "  $exec \$@\n";
  print WRAP "else\n";
  print WRAP "  ssh -akx \$subhost \"/bin/bash -c \\\" $exec \$@\\\"\"\n";
  print WRAP "fi\n";
  close WRAP;
  `chmod 755 $cmd`;
}
