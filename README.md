# DVE-Groups

My application for generating groups for first rounds of WCA competitions. 

It will be moved online to http://groups.danskspeedcubingforening.dk/

Additionally useful PDF's are generated to organisers. The program makes use of a slight modification of [Anker's scorecards](https://github.com/Daniel-Anker-Hermansen/WCA_tools_lib/tree/main/wca_scorecards_lib) for scorecards.

Notes on install, for ubuntu to get the fonts do `apt-get install fonts-dejavu-extra`. This should be the best approach. Otherwise, use the fonts and specify them as `fname` like in one of the early instances.

Todo:

* Double check that the overlapping events is working correctly.
* Add option for specifying a concrete number of groups for certain events.

QoL:

* Create extensions, and auto load them into the form.