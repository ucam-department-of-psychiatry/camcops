## inherit_cache_test_child.mako
## <%page cached="True" cache_region="local" cache_key="${self.filename}"/>
<%page cached="True" cache_region="local" cache_key="CHILD"/>
<%inherit file="inherit_cache_test_parent.mako"/>
Child_stuff
