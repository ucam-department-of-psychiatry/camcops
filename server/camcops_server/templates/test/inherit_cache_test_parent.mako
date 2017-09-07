## inherit_cache_test_parent.mako
## <%page cached="True" cache_region="local" cache_key="${self.filename}"/>
<%page cached="True" cache_region="local" cache_key="PARENT"/>
Parent_stuff_start
${self.body()}
Parent_stuff_end
