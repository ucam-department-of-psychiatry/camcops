## clinician_signature_block.mako

## Genuinely static, so we can cache it:
<%page cached="True" cache_region="local" cache_key="clinician_signature_block.mako"/>

<div>
    <table class="noborder">
        <tr class="signature_label">
            <td class="signature_label" width="33%">
                Signature of author/validator
            </td>
            <td class="signature_label" width="33%">
                Print name
            </td>
            <td class="signature_label" width="33%">
                Date and time
            </td>
        </tr>
        <tr class="signature">
            ## ... can't get "height" to work in table; only seems to like line-height; for
            ## which, you need some text, hence the &nbsp;
            ## http://stackoverflow.com/questions/6398172/setting-table-row-height-in-css
            <td class="signature">&nbsp;</td>
            <td class="signature">&nbsp;</td>
            <td class="signature">&nbsp;</td>
        </tr>
    </table>
</div>
