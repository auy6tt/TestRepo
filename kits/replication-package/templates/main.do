* main.do: master do-file that runs the whole replication package, start to finish.
*
* Usage: start Stata in the package's top folder (or cd there), then type:  do main.do
*        Batch mode on Linux or Mac:  stata-mp -b do main.do
*        On Windows, double-clicking main.do opens Stata in this folder.
*
* What it does:
*   1. Uses the current folder as the package root, so there is nothing to edit.
*   2. Makes Stata use only the community packages saved in ado/ (exact versions).
*   3. Creates the output folders and starts a log.
*   4. Runs each do-file in order. Stata stops at the first error.
*
* Inside the do-files, write every path as "$root/...", for example
*     use "$root/data/raw/survey.dta", clear
* and do not use cd.

version 18          // change to the Stata version the author used
clear all
set more off
set linesize 120

* ---- 1. Package root ------------------------------------------------------------
global root "`c(pwd)'"
capture confirm file "$root/main.do"
if _rc {
    display as error "Run main.do from the package's top folder: cd there first, then: do main.do"
    exit 601
}

* ---- 2. Community packages: use only the copies saved in ado/ -------------------
* These lines make ado/plus the place where Stata looks for (and installs) community
* packages. One-time set-up by the author: run this block, then for example
*     ssc install reghdfe, replace
*     ssc install ftools, replace
*     ssc install estout, replace
* and include the ado folder in the package. Replicators then get the same versions.
capture mkdir "$root/ado"
capture mkdir "$root/ado/plus"
capture mkdir "$root/ado/personal"
sysdir set PLUS     "$root/ado/plus"
sysdir set PERSONAL "$root/ado/personal"
* Some packages (for example ftools and reghdfe) need their Mata library indexed:
* mata: mata mlib index

* List the community commands the package needs, separated by spaces.
local needed ""     // for example: reghdfe ftools estout

* ---- 3. Folders and log -------------------------------------------------------------
capture mkdir "$root/output"
capture mkdir "$root/logs"
capture mkdir "$root/data/derived"
local stamp = subinstr("`c(current_date)'", " ", "", .) + "_" + subinstr("`c(current_time)'", ":", "", .)
capture log close _all
log using "$root/logs/main_`stamp'.log", replace text name(main)

display "Replication run started: `c(current_date)' `c(current_time)'"
display "Package folder: $root"
display "Stata `c(stata_version)', running under version `c(version)'"
display "Computer: `c(os)' `c(osdtl)', `c(processors)' processor(s) in use"

foreach cmd of local needed {
    capture noisily which `cmd'      // prints the package version into the log
    if _rc {
        display as error "Missing community package: `cmd'. It should be in $root/ado/plus (see README)."
        exit 199
    }
}

* ---- 4. Random numbers ---------------------------------------------------------------
* If a program uses random numbers and sets no seed of its own, agree a seed with the
* author and set it here. A new seed can change results slightly: report any change.
* set seed 20240101

* ---- 5. Run the programs in order ------------------------------------------------------
timer clear 1
timer on 1

do "$root/code/01_clean_data.do"
do "$root/code/02_analysis.do"
do "$root/code/03_figures.do"

timer off 1

* ---- 6. Finish ------------------------------------------------------------------------
display "Finished: `c(current_date)' `c(current_time)'"
timer list 1
log close main
