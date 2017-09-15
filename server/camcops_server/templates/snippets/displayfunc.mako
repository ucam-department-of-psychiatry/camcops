## displayfunc.mako

<%def name="one_per_line(iterable)">
    %for idx, x in enumerate(iterable):
        %if idx > 0:
            <br>
        %endif
        ${ x | h}
    %endfor
</%def>
