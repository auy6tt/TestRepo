# main.R: master script that runs the whole replication package, start to finish.
#
# Usage, from the package's top folder:
#     Rscript main.R
# Or open the package folder as an RStudio project and click Source.
#
# What it does:
#   1. Checks that it is running from the package's top folder.
#   2. Restores the exact package versions from renv.lock, if there is one.
#   3. Creates the folders the programs write to.
#   4. Runs each program in STEPS, in order, and prints its code and results.
#   5. Saves everything to logs/main_<date>_<time>.log, with sessionInfo() at the end.
#   6. Stops at the first error and says which program failed.
#
# To adapt it, edit STEPS and FOLDERS below. Inside the programs, use paths relative to
# the top folder, such as "data/raw/survey.csv", and never call setwd().

if (!file.exists("main.R")) {
  stop("Run this script from the package's top folder (the one that contains main.R). ",
       "In a terminal: cd to that folder, then run Rscript main.R. ",
       "In RStudio: Session > Set Working Directory > To Source File Location.",
       call. = FALSE)
}

# Programs to run, in order.
STEPS <- c(
  "code/01_clean_data.R",
  "code/02_analysis.R",
  "code/03_figures.R"
)

# Folders the programs write to. They are created if missing.
FOLDERS <- c("data/derived", "output", "logs")

# TRUE runs each program in a fresh environment, so programs share results only through
# saved files (the safest set-up). Set to FALSE if later programs use objects that earlier
# programs left in memory.
FRESH_ENVIRONMENT <- TRUE

# If a program uses random numbers and does not set its own seed, agree a seed with the
# author and set it here. A new seed can change results slightly: report any change.
# set.seed(20240101)

# Exact package versions. The author runs renv::init() once, then renv::snapshot() after
# the final run, and includes renv.lock in the package.
if (file.exists("renv.lock")) {
  if (!requireNamespace("renv", quietly = TRUE)) {
    install.packages("renv", repos = "https://cloud.r-project.org")
  }
  renv::restore(prompt = FALSE)
}

for (folder in FOLDERS) dir.create(folder, recursive = TRUE, showWarnings = FALSE)

log_file <- file.path("logs", format(Sys.time(), "main_%Y%m%d_%H%M%S.log"))
log_con <- file(log_file, open = "wt")
sink(log_con, split = TRUE)  # everything printed goes to the screen and the log

run_step <- function(script) {
  cat("\n=== ", script, " ===\n", sep = "")
  start <- Sys.time()
  env <- if (FRESH_ENVIRONMENT) new.env(parent = globalenv()) else globalenv()
  withCallingHandlers(
    source(script, local = env, echo = TRUE, max.deparse.length = Inf),
    # Show messages and warnings in the log too, not only on the screen.
    message = function(m) {
      cat(conditionMessage(m))
      invokeRestart("muffleMessage")
    },
    warning = function(w) {
      cat("Warning: ", conditionMessage(w), "\n", sep = "")
      invokeRestart("muffleWarning")
    }
  )
  seconds <- as.numeric(difftime(Sys.time(), start, units = "secs"))
  cat(sprintf("--- %s finished in %.1f s\n", script, seconds))
  seconds
}

cat("Replication run started", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "\n")
cat("Package folder:", basename(normalizePath(".")), "\n")  # name only: full paths can reveal user names
cat(R.version.string, "\n")
cat("Computer:", paste(Sys.info()[c("sysname", "release", "machine")], collapse = " "), "\n")

status <- 0
total <- 0
for (step in STEPS) {
  if (!file.exists(step)) {
    cat("ERROR: program not found:", step, "\n")
    status <- 1
    break
  }
  ok <- tryCatch({
    total <- total + run_step(step)
    TRUE
  }, error = function(e) {
    cat("\nFAILED: ", step, " stopped with this error:\n", conditionMessage(e), "\n", sep = "")
    FALSE
  })
  if (!ok) {
    status <- 1
    break
  }
}

if (status == 0) {
  cat(sprintf("\nAll %d programs finished in %.1f s. Log saved to %s\n", length(STEPS), total, log_file))
}
cat("\nSession information (R and package versions):\n")
print(sessionInfo())

sink()
close(log_con)
if (status != 0) quit(save = "no", status = status)
