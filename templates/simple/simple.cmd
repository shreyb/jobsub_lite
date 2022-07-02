
# generated by jobsub_lite 
# {%if debug is defined %}debug{%endif%}
universe           = vanilla
executable         = {{script_name|default('simple.sh')}}
arguments          = {{exe_arguments|join(" ")}}
{% set filebase %}{{executable|basename}}{{date}}{{uuid}}cluster.$(Cluster).$(Process){% endset %}
output             = {{filebase}}.out
error              = {{filebase}}.err
log                = {{filebase}}.log
environment        = CLUSTER=$(Cluster);PROCESS=$(Process);CONDOR_TMP={{outdir}};BEARER_TOKEN_FILE=.condor_creds/{{group}}.use;CONDOR_EXEC=/tmp;DAGMANJOBID=$(DAGManJobId);GRID_USER={{user}};JOBSUBJOBID=$(CLUSTER).$(PROCESS)@{{schedd}};EXPERIMENT={{group}};{{environment|join(';')}}
rank               = Mips / 2 + Memory
job_lease_duration = 3600
notification       = Never
transfer_output    = True
transfer_error     = True
transfer_executable= True
transfer_input_files = {{executable|basename}}
when_to_transfer_output = ON_EXIT_OR_EVICT
transfer_output_files = .empty_file
{%if    cpu is defined %}request_cpus = {{cpu}}{%endif%}
{%if memory is defined %}request_memory = {{memory}}{%endif%}
{%if   disk is defined %}request_disk = {{disk}}KB{%endif%}
{%if     OS is defined %}+DesiredOS={{OS}}{%endif%}
+JobsubClientDN="{{clientdn}}"
+JobsubClientIpAddress="{{ipaddr}}"
+Owner="{{user}}"
+JobsubServerVersion="{{jobsub_version}}"
+JobsubClientVersion="{{jobsub_version}}"
+JOB_EXPECTED_MAX_LIFETIME = {{expected_lifetime}}
notify_user = {{email_to}}

{% if subgroup is defined %}
+AccountingGroup = "group_{{group}}.{{subgroup}}.{{user}}"
{% else %}
+AccountingGroup = "group_{{group}}.{{user}}"
{% endif %}

+Jobsub_Group="{{group}}"
+JobsubJobId="$(CLUSTER).$(PROCESS)@{{schedd}}"
+Drain = False

{% if site is defined and site != 'LOCAL' %}
+DESIRED_SITES = "{{site}}"
{% endif %}
{%if blacklist is defined %}
+Blacklist_Sites = "{{blacklist}}"
{% endif %}
+GeneratedBy ="{{version}} {{schedd}}"
{{resource_provides_quoted|join("\n+DESIRED_")}}
{{lines|join("\n+")}}
requirements  = {%if overwrite_requirements is defined %}{{overwrite_requirements}}{%else%}target.machine =!= MachineAttrMachine1 && target.machine =!= MachineAttrMachine2  && (isUndefined(DesiredOS) || stringListsIntersect(toUpper(DesiredOS),IFOS_installed)) && (stringListsIntersect(toUpper(target.HAS_usage_model), toUpper(my.DESIRED_usage_model))){%endif%}{%if append_condor_requirements is defined %} && {{append_condor_requirements}} {%endif%}

{% if no_singularity is false %}
+SingularityImage="{{singularity_image}}"
{% endif %}

#
# this is supposed to get us output even if jobs are held(?)
#
+SpoolOnEvict = false
#
#
#
{% if role is defined and role != 'Analysis' %}
use_oauth_services = {{group}}_{{role}}
{% else %}
use_oauth_services = {{group}}
{% endif %}

queue {{N}}
