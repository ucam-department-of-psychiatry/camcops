## displayfunc.mako

<%def name="one_per_line(iterable, escape=True)">
    %for idx, x in enumerate(iterable):
        %if idx > 0:
            <br>
        %endif
        %if escape:
            ${ x | h}
        %else:
            ${ x }
        %endif
    %endfor
</%def>
