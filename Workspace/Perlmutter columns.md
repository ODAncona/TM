

job_id:
when the give you more info GPU, CPU, etc...
node_id and values for every timestamps

Account: 
way to find similarity (because the same project)

pratition:

GPU => gpu exclusively
shared_GPU => ask for a portion of GPU nodes

QOS:

regular => gpu job
preempt => lower priority queue
debug => small gpu jobs (max 30 mins)

start, end => timestamp

allocNode => the number of nodes a job got
AllocTRES => Not useful yet
NodeList => The primary key to connect with GPU traces + timestamp
ChargeFactor => Do not care
ElapsedSecs => check if it is end - start
queing time => submit - start
WaitTime
State => if job completed
TimeLimit => user estimated time limit
ConsumedEnergy => Check how reliable it is
office,program => department that launched the job one is with more details
sci_cat => 
allocation_type => useless
allocation_pool => useless
program_id => useless
sci_cat_id => try to correlate with sci_cat

