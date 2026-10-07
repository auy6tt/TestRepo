* Robustness: school FE and bootstrap -- JD 2022
cd "C:\Users\jdoe\Dropbox\tutoring-paper"
use "data\derived\robustness_sample.dta", clear

reghdfe endline_z tutoring baseline_z female low_income i.grade, absorb(school_id) vce(cluster school_id)
eststo r1

bootstrap _b, reps(500) cluster(school_id): regress endline_z tutoring baseline_z
eststo r2

esttab r1 r2 using "output\tableA2_robustness.tex", replace se star(* 0.10 ** 0.05 *** 0.01)
