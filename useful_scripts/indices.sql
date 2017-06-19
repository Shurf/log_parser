create index diagnoses_names on scan_logs.diagnoses (subtype, dia_type);
create index log_enties_names on scan_logs.log_entries (file_path(255));