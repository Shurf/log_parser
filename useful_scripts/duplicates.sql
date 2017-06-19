select diagnose_table.dia_type, diagnose_table.subtype
from 
	scan_logs.diagnoses diagnose_table,
    (SELECT dia_type, subtype, count(*) as cnt FROM scan_logs.diagnoses group by dia_type, subtype having cnt > 1) t
where diagnose_table.dia_type=t.dia_type and diagnose_table.subtype=t.subtype
order by diagnose_table.dia_type, diagnose_table.subtype


