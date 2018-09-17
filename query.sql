select 
	k1.keyword as Dependency, 
	k2.keyword as Dependent 
from 
	Keywords as k1,
	Keywords as K2,
	KeyDepends as d
where
	k1.key_id = d.depon and
	k2.key_id = d.depto
order by
	k1.key_id, k2.key_id
;
