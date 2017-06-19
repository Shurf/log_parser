
select 
	le1.id as id1,
    le2.id as id2,
    lf1.full_path as lf1p,
    lf2.full_path as lf2p#,
    #a1.diagnose_id as diagnose_id
    
from 
	scan_logs.log_entries le1, 
    scan_logs.log_entries le2,
    #scan_logs.assotiation_file_diagnose a1,
    scan_logs.log_files lf1,
    scan_logs.log_files lf2
where 
	le1.file_path = le2.file_path and 
    #a1.entry_id = le1.id and
    #le1.id < le2.id and
    le1.log_file = lf1.id and
    le2.log_file = lf2.id and
    exists (
		select 
			*
		from 
			scan_logs.assotiation_file_diagnose d 
		where 
			d.entry_id=le1.id and 
            not exists (
				select 
					*
				from 
					scan_logs.assotiation_file_diagnose d_inner 
				where 
					d_inner.diagnose_id = d.diagnose_id and 
                    d_inner.entry_id=le2.id))
    #lf1.engine_version <> lf2.engine_version and
    #a1.diagnose_id not in (select diagnose_id from  scan_logs.assotiation_file_diagnose t where t.entry_id = le2.id)
#limit 100