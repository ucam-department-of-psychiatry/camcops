#!/bin/bash

# use --table for tabular view

SQL="
    SELECT c.table_name, c.column_name, c.data_type, c.is_nullable, c.column_comment
    FROM information_schema.columns c
        INNER JOIN information_schema.tables t
        ON c.table_schema = t.table_schema
        AND c.table_name = t.table_name
    WHERE t.table_type='BASE TABLE'
    AND c.table_schema='camcops'
    ;
"

echo $SQL \
	| mysql -u root -p \
	| sed "s/^/<tr><td>/;s/\t/<\/td><td>/g;s/$/<\/td<\/tr>/" \
	> camcops_column_definitions.txt

# in turn:
# mysql will produce tab-separated output
# sed will
# ... put <tr><td> at the beginning of each line
# ... tabs to </td><td>, globally
# ... put </td></tr> at the end of each line


# http://stackoverflow.com/questions/6541109/send-string-to-stdin
# http://stackoverflow.com/questions/356578/how-to-output-mysql-query-results-in-csv-format
