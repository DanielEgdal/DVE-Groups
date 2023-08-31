# DVE-Groups

My application for generating groups for first rounds of WCA competitions. 

It can be found at http://groups.danskspeedcubingforening.dk/

Additionally useful PDF's are generated to organisers. The program makes use of a slight modification of [Anker's scorecards](https://github.com/Daniel-Anker-Hermansen/WCA_tools_lib/tree/main/wca_scorecards_lib) for scorecards.

Notes on install, for ubuntu to get the fonts do `apt-get install fonts-dejavu-extra`. This should be the best approach. Otherwise, use the fonts and specify them as `fname` like in one of the early instances.

Todo:

* Look through the TODO comments
* There is no manual editing atm. Working on being able to import existing WCIFs which have been partly generated by this script and modified by hand through https://delegate-dashboard.netlify.app/
* Add some support to double check every registered competitor is added to their event.

QoL:

* Create more extensions, and auto load them into the form.