#!/usr/bin/env python

r"""
camcops_server/cc_modules/cc_snomed.py

===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

**CamCOPS code to support SNOMED-CT.**

Note that the licensing arrangements for SNOMED-CT mean that the actual codes
must be separate (and not part of the CamCOPS code). See the documentation.

A full SNOMED CT download is about 1.1 Gb; see
https://digital.nhs.uk/services/terminology-and-classifications/snomed-ct.
Within a file such as ``uk_sct2cl_26.0.2_20181107000001.zip``, relevant files
include:

.. code-block:: none

    # Files with "Amoxicillin" in include two snapshots and two full files:
    
    SnomedCT_UKClinicalRF2_PRODUCTION_20181031T000001Z/Full/Terminology/sct2_Description_Full-en-GB_GB1000000_20181031.txt
    # ... 234,755 lines
    
    SnomedCT_InternationalRF2_PRODUCTION_20180731T120000Z/Full/Terminology/sct2_Description_Full-en_INT_20180731.txt
    # ... 2,513,953 lines; this is the main file.

Note grammar:

- http://snomed.org/scg
- https://confluence.ihtsdotools.org/display/DOCSCG
- https://confluence.ihtsdotools.org/download/attachments/33494865/SnomedCtExpo_Expressions_20161028_s2_20161101.pdf  # noqa
- https://confluence.ihtsdotools.org/display/SLPG/SNOMED+CT+Expression+Constraint+Language

Test basic expressions:

    .. code-block:: python

        import logging
        from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
        from camcops_server.cc_modules.cc_request import get_command_line_request
        from camcops_server.cc_modules.cc_snomed import *
        from camcops_server.tasks.phq9 import Phq9
        main_only_quicksetup_rootlogger(level=logging.DEBUG)
        req = get_command_line_request()
        
        # ---------------------------------------------------------------------
        # From the SNOMED-CT examples (http://snomed.org/scg), with some values
        # fixed from the term browser:
        # ---------------------------------------------------------------------
        
        diabetes = SnomedConcept(73211009, "Diabetes mellitus (disorder)")
        diabetes_expr = SnomedExpression(diabetes)
        print(diabetes_expr.longform)
        print(diabetes_expr.shortform)
        
        pain = SnomedConcept(22253000, "Pain (finding)")
        finding_site = SnomedConcept(36369800, "Finding site")
        foot = SnomedConcept(56459004, "Foot")
        
        pain_in_foot = SnomedExpression(pain, {finding_site: foot})
        print(pain_in_foot.longform)
        print(pain_in_foot.shortform)
        
        amoxicillin_medicine = SnomedConcept(27658006, "Product containing amoxicillin (medicinal product)")
        amoxicillin_substance = SnomedConcept(372687004, "Amoxicillin (substance)")
        has_dose_form = SnomedConcept(411116001, "Has manufactured dose form (attribute)")
        capsule = SnomedConcept(385049006, "Capsule (basic dose form)")
        has_active_ingredient = SnomedConcept(127489000, "Has active ingredient (attribute)")
        has_basis_of_strength_substance = SnomedConcept(732943007, "Has basis of strength substance (attribute)")
        mass = SnomedConcept(118538004, "Mass, a measure of quantity of matter (property) (qualifier value)")
        unit_of_measure = SnomedConcept(767524001, "Unit of measure (qualifier value)")
        milligrams = SnomedConcept(258684004, "milligram (qualifier value)")
        
        amoxicillin_500mg_capsule = SnomedExpression(
            amoxicillin_medicine, [
                SnomedAttributeSet({has_dose_form: capsule}),
                SnomedAttributeGroup({
                    has_active_ingredient: amoxicillin_substance,
                    has_basis_of_strength_substance: SnomedExpression(
                        amoxicillin_substance, {
                            mass: 500,
                            unit_of_measure: milligrams,
                        }
                    ),
                }),
            ]
        )
        print(amoxicillin_500mg_capsule.longform)
        print(amoxicillin_500mg_capsule.shortform)
        
        # ---------------------------------------------------------------------
        # Read the XML, etc.
        # ---------------------------------------------------------------------
        
        print(VALID_SNOMED_LOOKUPS)
        concepts = get_all_snomed_concepts(req.config.snomed_xml_filename)
        
        # ---------------------------------------------------------------------
        # Test a task, and loading SNOMED data from XML via the CamCOPS config
        # ---------------------------------------------------------------------
        
        phq9 = Phq9()
        print("\n".join(str(x) for x in phq9.get_snomed_codes(req)))
        phq9.q1 = 2
        phq9.q2 = 2
        phq9.q3 = 2
        phq9.q4 = 2
        phq9.q5 = 2
        phq9.q6 = 2
        phq9.q7 = 2
        phq9.q8 = 2
        phq9.q9 = 2
        phq9.q10 = 2
        print("\n".join(repr(x) for x in phq9.get_snomed_codes(req)))
        print("\n".join(str(x) for x in phq9.get_snomed_codes(req)))
        

"""  # noqa

import logging
from typing import Dict, Iterable, List, Set, Union
import xml.etree.cElementTree as ElementTree

from cardinal_pythonlib.reprfunc import simple_repr

from camcops_server.cc_modules.cc_cache import cache_region_static, fkg
from camcops_server.cc_modules.cc_xml import XmlDataTypes, XmlElement

log = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

BACKSLASH = "\\"
COLON = ":"
COMMA = ","
EQUALS = "="
HASH = "#"
LBRACE = "{"
LBRACKET = "("
PIPE = "|"
PLUS = "+"
QM = '"'  # double quotation mark
RBRACE = "}"
RBRACKET = ")"
TAB = "\t"
NEWLINE = "\n"

ID_MIN_DIGITS = 6
ID_MAX_DIGITS = 18

VALUE_TYPE = Union["SnomedConcept", "SnomedExpression", int, float, str]
DICT_ATTR_TYPE = Dict["SnomedConcept", VALUE_TYPE]

SNOMED_XML_NAME = "snomed_ct_expression"


# =============================================================================
# Quoting strings
# =============================================================================

def double_quoted(s: str) -> str:
    """
    Returns a representation of the string argument with double quotes and
    escaped characters.

    Args:
        s: the argument

    See:

    - http://code.activestate.com/lists/python-list/272714/ -- does not work
      as null values get escaped in different ways in modern Python, and in a
      slightly unpredictable way
    - https://mail.python.org/pipermail/python-list/2003-April/236940.html --
      won't deal with repr() using triple-quotes
    - https://stackoverflow.com/questions/1675181/get-str-repr-with-double-quotes-python
      -- probably the right general approach

    Test code:

    .. code-block:: python

        from camcops_server.cc_modules.cc_snomed import double_quoted
        
        def test(s):
            print("double_quoted({!r}) -> {}".format(s, double_quoted(s)))
        
        
        test("ab'cd")
        test("ab'c\"d")
        test('ab"cd')

    """  # noqa
    # For efficiency, we use a list:
    # https://stackoverflow.com/questions/3055477/how-slow-is-pythons-string-concatenation-vs-str-join  # noqa
    # https://waymoot.org/home/python_string/
    dquote = '"'
    ret = [dquote]  # type: List[str]
    for c in s:
        # "Named" characters
        if c == NEWLINE:
            ret.append(r"\n")
        elif c == TAB:
            ret.append(r"\t")
        elif c == QM:
            ret.append(r'\"')
        elif c == BACKSLASH:
            ret.append(r"\\")
        elif ord(c) < 32:
            ret.append(r"\x{:02X}".format(ord(c)))
        else:
            ret.append(c)
    ret.append(dquote)
    return "".join(ret)


# =============================================================================
# SNOMED-CT concepts
# =============================================================================

class SnomedBase(object):
    """
    Common functions for SNOMED-CT classes
    """
    def as_string(self, longform: bool = True) -> str:
        """
        Returns the string form.

        Args:
            longform: print SNOMED-CT concepts in long form?
        """
        raise NotImplementedError()

    @property
    def shortform(self) -> str:
        """
        Returns the short form, without terms.
        """
        return self.as_string(False)

    @property
    def longform(self) -> str:
        return self.as_string(True)

    def __str__(self) -> str:
        return self.as_string(True)

    def xml_element(self, longform: bool = True) -> XmlElement:
        """
        Returns a :class:`camcops_server.cc_modules.cc_xml.XmlElement` for this
        SNOMED-CT object.

        Args:
            longform: print SNOMED-CT concepts in long form?
        """
        return XmlElement(
            name=SNOMED_XML_NAME,
            value=self.as_string(longform),
            datatype=XmlDataTypes.STRING
        )


class SnomedConcept(SnomedBase):
    """
    Represents a SNOMED concept with its description (associated term).
    """
    def __init__(self, identifier: int, term: str) -> None:
        """
        Args:
            identifier: SNOMED-CT identifier (code)
            term: associated term (description)
        """
        assert isinstance(identifier, int), (
            "SNOMED-CT concept identifier is not an integer: "
            "{!r}".format(identifier)
        )
        ndigits = len(str(identifier))
        assert ID_MIN_DIGITS <= ndigits <= ID_MAX_DIGITS, (
            "SNOMED-CT concept identifier has wrong number of digits: "
            "{!r}".format(identifier)
        )
        assert PIPE not in term, (
            "SNOMED-CT term has invalid pipe character: {!r}".format(term)
        )
        self.identifier = identifier
        self.term = term

    def __repr__(self) -> str:
        return simple_repr(self, ["identifier", "term"])

    def as_string(self, longform: bool = True) -> str:
        # Docstring in base class.
        if longform:
            return "{ident} {delim}{term}{delim}".format(
                ident=self.identifier,
                delim=PIPE,
                term=self.term,
            )
        else:
            return str(self.identifier)

    def concept_reference(self, longform: bool = True) -> str:
        """
        Returns one of the string representations.

        Args:
            longform: in long form, with the description (associated term)?
        """
        return self.as_string(longform)


# =============================================================================
# SNOMED-CT expressions
# =============================================================================

class SnomedValue(SnomedBase):
    """
    Represents a value: either a concrete value (e.g. int, float, str), or a
    SNOMED-CT concept/expression.

    Implements the grammar elements: attributeValue, expressionValue,
    stringValue, numericValue, integerValue, decimalValue.
    """
    def __init__(self, value: VALUE_TYPE) -> None:
        """
        Args:
            value: the value
        """
        assert isinstance(value, (SnomedConcept, SnomedExpression,
                                  int, float, str)), (
            "Invalid value type to SnomedValue: {!r}".format(value)
        )
        self.value = value

    def as_string(self, longform: bool = True) -> str:
        # Docstring in base class
        x = self.value
        if isinstance(x, SnomedConcept):
            return x.concept_reference(longform)
        elif isinstance(x, SnomedExpression):
            # As per p16 of formal reference cited above.
            return "{lbracket} {expr} {rbracket}".format(
                lbracket=LBRACKET,
                expr=x.as_string(longform),
                rbracket=RBRACKET,
            )
        elif isinstance(x, (int, float)):
            return HASH + str(x)
        elif isinstance(x, str):
            # On the basis that SNOMED's "QM" (quote mark) is 0x22, the double
            # quote:
            return double_quoted(x)
        else:
            raise ValueError("Bad input value type")

    def __repr__(self) -> str:
        return simple_repr(self, ["value"])


class SnomedFocusConcept(SnomedBase):
    """
    Represents a SNOMED-CT focus concept, which is one or more concepts.
    """
    def __init__(self,
                 concept: Union[SnomedConcept, Iterable[SnomedConcept]]) \
            -> None:
        """
        Args:
            concept: the core concept(s); a :class:`SnomedCode` or an
                iterable of them
        """
        if isinstance(concept, SnomedConcept):
            self.concepts = [concept]
        else:
            self.concepts = list(concept)
        assert all(isinstance(x, SnomedConcept) for x in self.concepts)

    def as_string(self, longform: bool = True) -> str:
        # Docstring in base class.
        sep = PLUS + " "
        return sep.join(c.concept_reference(longform) for c in self.concepts)

    def __repr__(self) -> str:
        return simple_repr(self, ["concepts"])


class SnomedAttribute(SnomedBase):
    """
    Represents a SNOMED-CT attribute, being a name/value pair.
    """
    def __init__(self, name: SnomedConcept, value: VALUE_TYPE) -> None:
        """
        Args:
            name: a :class:`SnomedConcept` (attribute name)
            value: an attribute value (:class:`SnomedConcept`, number, or
                string)
        """
        assert isinstance(name, SnomedConcept)
        if not isinstance(value, SnomedValue):
            value = SnomedValue(value)
        self.name = name
        self.value = value

    def as_string(self, longform: bool = True) -> str:
        # Docstring in base class.
        return "{name} {eq} {value}".format(
            name=self.name.concept_reference(longform),
            eq=EQUALS,
            value=self.value.as_string(longform)
        )

    def __repr__(self) -> str:
        return simple_repr(self, ["name", "value"])


class SnomedAttributeSet(SnomedBase):
    """
    Represents an attribute set.
    """
    def __init__(self, attributes: Union[DICT_ATTR_TYPE,
                                         Iterable[SnomedAttribute]]) -> None:
        """
        Args:
            attributes: the attributes
        """
        if isinstance(attributes, dict):
            self.attributes = [SnomedAttribute(k, v)
                               for k, v in attributes.items()]
        else:
            self.attributes = list(attributes)
        assert all(isinstance(x, SnomedAttribute) for x in self.attributes)

    def as_string(self, longform: bool = True) -> str:
        # Docstring in base class.
        attrsep = COMMA + " "
        return attrsep.join(attr.as_string(longform)
                            for attr in self.attributes)

    def __repr__(self) -> str:
        return simple_repr(self, ["attributes"])


class SnomedAttributeGroup(SnomedBase):
    """
    Represents a collected group of attribute/value pairs.
    """
    def __init__(self, attribute_set: Union[DICT_ATTR_TYPE,
                                            SnomedAttributeSet]) -> None:
        """
        Args:
            attribute_set: a :class:`SnomedAttributeSet` to group
        """
        if isinstance(attribute_set, dict):
            attribute_set = SnomedAttributeSet(attribute_set)
        assert isinstance(attribute_set, SnomedAttributeSet)
        self.attribute_set = attribute_set

    def as_string(self, longform: bool = True) -> str:
        # Docstring in base class.
        return "{lbrace} {attrset} {rbrace}".format(
            lbrace=LBRACE,
            attrset=self.attribute_set.as_string(longform),
            rbrace=RBRACE,
        )

    def __repr__(self) -> str:
        return simple_repr(self, ["attribute_set"])


class SnomedRefinement(SnomedBase):
    """
    Implements a SNOMED-CT "refinement", which is an attribute set +/- some
    attribute groups.
    """
    def __init__(self,
                 refinements: Union[DICT_ATTR_TYPE,
                                    Iterable[Union[SnomedAttributeSet,
                                                   SnomedAttributeGroup]]]) \
            -> None:
        """
        Args:
            refinements: iterable of :class:`SnomedAttributeSet` (but only
                zero or one) and :class:`SnomedAttributeGroup` objects
        """
        if isinstance(refinements, dict):
            refinements = [SnomedAttributeSet(refinements)]
        self.attrsets = []  # type: List[SnomedBase]
        self.attrgroups = []  # type: List[SnomedBase]
        for r in refinements:
            if isinstance(r, SnomedAttributeSet):
                if self.attrsets:
                    raise ValueError("Only one SnomedAttributeSet allowed "
                                     "to SnomedRefinement")
                self.attrsets.append(r)
            elif isinstance(r, SnomedAttributeGroup):
                self.attrgroups.append(r)
            else:
                raise ValueError("Unknown object to SnomedRefinement: "
                                 "{!r}".format(r))

    def as_string(self, longform: bool = True) -> str:
        # Docstring in base class.
        sep = COMMA + " "
        return sep.join(x.as_string(longform)
                        for x in self.attrsets + self.attrgroups)

    def __repr__(self) -> str:
        return simple_repr(self, ["attrsets", "attrgroups"])


class SnomedExpression(SnomedBase):
    """
    An expression containing several SNOMED-CT codes in relationships.
    """
    def __init__(self,
                 focus_concept: Union[SnomedConcept, SnomedFocusConcept],
                 refinement: Union[SnomedRefinement,
                                   DICT_ATTR_TYPE,
                                   List[Union[SnomedAttributeSet,
                                              SnomedAttributeGroup]]] = None) \
            -> None:
        """
        Args:
            focus_concept: the core concept(s); a :class:`SnomedFocusConcept`
            refinement: optional additional information; a
                :class:`SnomedRefinement` or a dictionary or list that can be
                converted to one
        """
        if isinstance(focus_concept, SnomedConcept):
            focus_concept = SnomedFocusConcept(focus_concept)
        assert isinstance(focus_concept, SnomedFocusConcept)
        if isinstance(refinement, (dict, list)):
            refinement = SnomedRefinement(refinement)
        if refinement is not None:
            assert isinstance(refinement, SnomedRefinement)
        self.focus_concept = focus_concept
        self.refinement = refinement

    def as_string(self, longform: bool = True) -> str:
        # Docstring in base class.
        s = self.focus_concept.as_string(longform)
        if self.refinement:
            s += " " + COLON + " " + self.refinement.as_string(longform)
        return s

    def __repr__(self) -> str:
        return simple_repr(self, ["focus_concept", "refinement"])


# =============================================================================
# Lookup codes
# =============================================================================

class SnomedLookup(object):
    """
    We're not allowed to embed SNOMED-CT codes in the CamCOPS code. Therefore,
    within CamCOPS, we use string constants represented in this class. If the
    local institution is allowed (e.g. in the UK, as below), then it can
    install additional data.
    
    - UK license:
      https://isd.digital.nhs.uk/trud3/user/guest/group/0/pack/26/subpack/101/licences
    
    - To find codes: https://termbrowser.nhs.uk/
    
    Abbreviations:
    
    - "Finding" is not abbreviated
    - "Obs" or "observable" is short for "observable entity"
    - "Procedure" is not abbreviated
    - "Scale" is short for "assessment scale"
    - "Situation" is not abbreviated
    
    Variable names are designed for clear code. Value strings are designed for
    clear XML that matches SNOMED-CT, in the format TASK_CONCEPTTYPE_NAME.
    
    """  # noqa
    # https://snomedbrowser.com/Codes/Details/XXX  # noqa

    # -------------------------------------------------------------------------
    # SNOMED-CT core concepts
    # -------------------------------------------------------------------------

    # Abstract physical quantities
    MASS = "mass"
    LENGTH = "length"

    # Saying "units"
    UNIT_OF_MEASURE = "unit_of_measure"

    # Base physical units
    KILOGRAM = "kilogram"
    METRE = "metre"

    # Compound physical units
    KG_PER_SQ_M = "kilogram_per_square_metre"

    # -------------------------------------------------------------------------
    # Scales
    # -------------------------------------------------------------------------

    # ACE-R
    ACE_R_SCALE = "ace_r_scale"
    ACE_R_SUBSCALE_ATTENTION_ORIENTATION = "ace_r_subscale_attention_orientation"  # noqa
    ACE_R_SUBSCALE_FLUENCY = "ace_r_subscale_fluency"
    ACE_R_SUBSCALE_LANGUAGE = "ace_r_subscale_language"
    ACE_R_SUBSCALE_MEMORY = "ace_r_subscale_memory"
    ACE_R_SUBSCALE_VISUOSPATIAL = "ace_r_subscale_visuospatial"
    ACE_R_SCORE = "ace_r_observable_score"
    ACE_R_SUBSCORE_ATTENTION_ORIENTATION = "ace_r_observable_subscore_attention_orientation"  # noqa
    ACE_R_SUBSCORE_FLUENCY = "ace_r_observable_subscore_fluency"
    ACE_R_SUBSCORE_LANGUAGE = "ace_r_observable_subscore_language"
    ACE_R_SUBSCORE_MEMORY = "ace_r_observable_subscore_memory"
    ACE_R_SUBSCORE_VISUOSPATIAL = "ace_r_observable_subscore_visuospatial"
    ACE_R_PROCEDURE_ASSESSMENT = "ace_r_procedure_assessment"
    ACE_R_PROCEDURE_ASSESSMENT_SUBSCALE_ATTENTION_ORIENTATION = "ace_r_procedure_assessment_subscale_attention_orientation"  # noqa
    ACE_R_PROCEDURE_ASSESSMENT_SUBSCALE_FLUENCY = "ace_r_procedure_assessment_subscale_fluency"  # noqa
    ACE_R_PROCEDURE_ASSESSMENT_SUBSCALE_LANGUAGE = "ace_r_procedure_assessment_subscale_language"  # noqa
    ACE_R_PROCEDURE_ASSESSMENT_SUBSCALE_MEMORY = "ace_r_procedure_assessment_subscale_memory"  # noqa
    ACE_R_PROCEDURE_ASSESSMENT_SUBSCALE_VISUOSPATIAL = "ace_r_procedure_assessment_subscale_visuospatial"  # noqa

    # AIMS
    AIMS_SCALE = "aims_scale"
    AIMS_TOTAL_SCORE = "aims_observable_total_score"
    AIMS_PROCEDURE_ASSESSMENT = "aims_procedure_assessment"

    # AUDIT, AUDIT-C
    AUDIT_SCALE = "audit_scale"
    AUDIT_SCORE = "audit_observable_score"
    AUDIT_PROCEDURE_ASSESSMENT = "audit_procedure_assessment"
    AUDITC_SCALE = "auditc_scale"
    AUDITC_SCORE = "auditc_observable_score"
    AUDITC_PROCEDURE_ASSESSMENT = "auditc_procedure_assessment"

    # BADLS
    BADLS_SCALE = "badls_scale"
    BADLS_SCORE = "badls_observable_score"
    BADLS_PROCEDURE_ASSESSMENT = "badls_procedure_assessment"

    # BDI
    BDI_SCALE = "bdi_scale"
    BDI_SCORE = "bdi_observable_score"
    BDI_PROCEDURE_ASSESSMENT = "bdi_procedure_assessment"
    BDI_II_SCORE = "bdi_ii_observable_score"
    BDI_II_PROCEDURE_ASSESSMENT = "bdi_ii_procedure_assessment"

    # BMI
    BMI_OBSERVABLE = "bmi_observable"
    BMI_PROCEDURE_MEASUREMENT = "bmi_procedure_measurement"
    BODY_HEIGHT_OBSERVABLE = "body_height_observable"
    BODY_WEIGHT_OBSERVABLE = "body_weight_observable"

    # BPRS, BPRS-E
    BPRS1962_SCALE = "bprs1962_scale"
    # no observable/procedure

    # CAGE
    CAGE_SCALE = "cage_scale"
    CAGE_SCORE = "cage_observable_score"
    CAGE_PROCEDURE_ASSESSMENT = "cage_procedure_assessment"

    # CAPE-42: none
    # CAPS: none
    # Cardinal RN, Expectation-Detection: none
    # CBI-R: none
    # CECA-Q3: none
    # CESD, CESD-R: none
    # CGI, CGI-I, CGI-SCH: none
    # CIS-R: none

    # CIWA-Ar
    CIWA_AR_SCALE = "ciwa_ar_scale"
    CIWA_AR_SCORE = "ciwa_ar_observable_score"
    CIWA_AR_PROCEDURE_ASSESSMENT = "ciwa_ar_procedure_assessment"

    # Clinical: progress note
    PROGRESS_NOTE_PROCEDURE = "progress_note_procedure"

    # Clinical: photograph
    PHOTOGRAPH_PROCEDURE = "photograph_procedure"
    PHOTOGRAPH_PHYSICAL_OBJECT = "photograph_physical_object"

    # Clinical: psychiatric clerking
    PSYCHIATRIC_ASSESSMENT_PROCEDURE = "psychiatric_assessment_procedure"
    # Not sure we can code other things more accurately!

    # CPFT/CUH LPS: none
    # COPE: none

    # CORE-10
    CORE10_SCALE = "core10_scale"
    CORE10_SCORE = "core10_observable_score"
    CORE10_PROCEDURE_ASSESSMENT = "core10_procedure_assessment"

    # DAD: none

    # DAST
    DAST_SCALE = "dast_scale"
    # I think the similarly named codes represent urine screening.

    # Deakin JB, antibody: none
    # Demo questionnaire: none
    # DEMQOL, DEMQOL-Proxy: none
    # Distress Thermometer: none

    # EQ-5D-5L
    EQ5D5L_SCALE = "eq5d5l_scale"
    EQ5D5L_INDEX_VALUE = "eq5d5l_observable_index_value"
    EQ5D5L_PAIN_DISCOMFORT_SCORE = "eq5d5l_observable_pain_discomfort_score"
    EQ5D5L_USUAL_ACTIVITIES_SCORE = "eq5d5l_observable_usual_activities_score"
    EQ5D5L_ANXIETY_DEPRESSION_SCORE = "eq5d5l_observable_anxiety_depression_score"  # noqa
    EQ5D5L_MOBILITY_SCORE = "eq5d5l_observable_mobility_score"
    EQ5D5L_SELF_CARE_SCORE = "eq5d5l_observable_self_care_score"
    EQ5D5L_PROCEDURE_ASSESSMENT = "eq5d5l_procedure_assessment"

    # FACT-G: none

    # FAST: none
    FAST_SCALE = "fast_scale"
    FAST_SCORE = "fast_observable_score"
    FAST_PROCEDURE_ASSESSMENT = "fast_procedure_assessment"

    # IRAC: none
    # FFT: none

    # Patient Satisfaction Scale
    # Not sure. See XML

    # Referrer Satisfaction Scale (patient-specific, survey): none
    # Frontotemporal Dementia Rating Scale: none

    # GAD-7
    GAD7_SCALE = "gad7_scale"
    GAD7_SCORE = "gad7_observable_score"
    GAD7_PROCEDURE_ASSESSMENT = "gad7_procedure_assessment"

    # GAF
    GAF_SCALE = "gaf_scale"
    # no observable/procedure

    # GDS-15
    GDS15_SCALE = "gds15_scale"
    GDS15_SCORE = "gds15_observable_score"
    GDS15_PROCEDURE_ASSESSMENT = "gds15_procedure_assessment"

    # UK GMC Patient Questionnaire: none

    # HADS, HADS-respondent
    HADS_SCALE = "hads_scale"
    HADS_ANXIETY_SCORE = "hads_observable_anxiety_score"
    HADS_DEPRESSION_SCORE = "hads_observable_depression_score"
    HADS_PROCEDURE_ASSESSMENT = "hads_procedure_assessment"

    # HAMA: none

    # HAMD
    HAMD_SCALE = "hamd_scale"
    HAMD_SCORE = "hamd_observable_score"
    HAMD_PROCEDURE_ASSESSMENT = "hamd_procedure_assessment"

    # HAMD-7: none

    # HoNOS, HoNOS-65+, HoNOSCA, etc. (there are others too)
    HONOSCA_SCALE = "honos_childrenadolescents_scale"
    HONOSCA_SECTION_A_SCALE = "honos_childrenadolescents_section_a_scale"
    HONOSCA_SECTION_B_SCALE = "honos_childrenadolescents_section_b_scale"
    HONOSCA_SCORE = "honos_childrenadolescents_observable_score"
    HONOSCA_SECTION_A_SCORE = "honos_childrenadolescents_observable_section_a_score"  # noqa
    HONOSCA_SECTION_B_SCORE = "honos_childrenadolescents_observable_section_b_score"  # noqa
    HONOSCA_SECTION_A_PLUS_B_SCORE = "honos_childrenadolescents_observable_section_a_plus_b_score"  # noqa
    HONOSCA_PROCEDURE_ASSESSMENT = "honos_childrenadolescents_procedure_assessment"  # noqa
    #
    HONOS65_SCALE = "honos_olderadults_scale"
    HONOS65_SCORE = "honos_olderadults_observable_score"
    HONOS65_PROCEDURE_ASSESSMENT = "honos_olderadults_procedure_assessment"
    #
    HONOSWA_SCALE = "honos_workingage_scale"
    HONOSWA_SUBSCALE_1_OVERACTIVE = "honos_workingage_subscale_1_overactive"
    HONOSWA_SUBSCALE_2_SELFINJURY = "honos_workingage_subscale_2_selfinjury"
    HONOSWA_SUBSCALE_3_SUBSTANCE = "honos_workingage_subscale_3_substance"
    HONOSWA_SUBSCALE_4_COGNITIVE = "honos_workingage_subscale_4_cognitive"
    HONOSWA_SUBSCALE_5_PHYSICAL = "honos_workingage_subscale_5_physical"
    HONOSWA_SUBSCALE_6_PSYCHOSIS = "honos_workingage_subscale_6_psychosis"
    HONOSWA_SUBSCALE_7_DEPRESSION = "honos_workingage_subscale_7_depression"
    HONOSWA_SUBSCALE_8_OTHERMENTAL = "honos_workingage_subscale_8_othermental"
    HONOSWA_SUBSCALE_9_RELATIONSHIPS = "honos_workingage_subscale_9_relationships"  # noqa
    HONOSWA_SUBSCALE_10_ADL = "honos_workingage_subscale_10_adl"
    HONOSWA_SUBSCALE_11_LIVINGCONDITIONS = "honos_workingage_subscale_11_livingconditions"  # noqa
    HONOSWA_SUBSCALE_12_OCCUPATION = "honos_workingage_subscale_12_occupation"
    HONOSWA_SCORE = "honos_workingage_observable_score"
    HONOSWA_1_OVERACTIVE_SCORE = "honos_workingage_observable_1_overactive_score"  # noqa
    HONOSWA_2_SELFINJURY_SCORE = "honos_workingage_observable_2_selfinjury_score"  # noqa
    HONOSWA_3_SUBSTANCE_SCORE = "honos_workingage_observable_3_substance_score"
    HONOSWA_4_COGNITIVE_SCORE = "honos_workingage_observable_4_cognitive_score"
    HONOSWA_5_PHYSICAL_SCORE = "honos_workingage_observable_5_physical_score"
    HONOSWA_6_PSYCHOSIS_SCORE = "honos_workingage_observable_6_psychosis_score"
    HONOSWA_7_DEPRESSION_SCORE = "honos_workingage_observable_7_depression_score"  # noqa
    HONOSWA_8_OTHERMENTAL_SCORE = "honos_workingage_observable_8_othermental_score"  # noqa
    HONOSWA_9_RELATIONSHIPS_SCORE = "honos_workingage_observable_9_relationships_score"  # noqa
    HONOSWA_10_ADL_SCORE = "honos_workingage_observable_10_adl_score"
    HONOSWA_11_LIVINGCONDITIONS_SCORE = "honos_workingage_observable_11_livingconditions_score"  # noqa
    HONOSWA_12_OCCUPATION_SCORE = "honos_workingage_observable_12_occupation_score"  # noqa
    HONOSWA_PROCEDURE_ASSESSMENT = "honos_workingage_procedure_assessment"

    # ICD-9-CM ***

    # ICD-10 ***

    # IDED3D: none

    # IES-R
    IESR_SCALE = "iesr_scale"
    IESR_SCORE = "iesr_observable_score"
    IESR_PROCEDURE_ASSESSMENT = "iesr_procedure_assessment"

    # INECO Frontal Screening: none
    # Khandaker G, Insight: none

    # MAST, SMAST
    MAST_SCALE = "mast_scale"
    MAST_SCORE = "mast_observable_score"
    MAST_PROCEDURE_ASSESSMENT = "mast_procedure_assessment"

    SMAST_SCALE = "smast_scale"
    # SMAST: no observable/procedure

    # MDS-UPDRS
    UPDRS_SCALE = "updrs_scale"
    # MDS-UPDRS: no observable/procedure

    # MoCA
    MOCA_SCALE = "moca_scale"
    MOCA_SCORE = "moca_observable_score"
    MOCA_PROCEDURE_ASSESSMENT = "moca_procedure_assessment"

    # NART
    NART_SCALE = "nart_scale"
    NART_SCORE = "nart_observable_score"
    NART_PROCEDURE_ASSESSMENT = "nart_procedure_assessment"

    # NPI-Q: none

    # PANSS
    PANSS_SCALE = "panss_scale"
    # PANSS: no observable/procedure

    # PCL and variants: none

    # PDSS
    PDSS_SCALE = "pdss_scale"
    PDSS_SCORE = "pdss_observable_score"
    # PDSS: no procedure

    # "Perinatal" and "scale": none

    # PHQ-9
    PHQ9_FINDING_NEGATIVE_SCREENING_FOR_DEPRESSION = "phq9_finding_negative_screening_for_depression"  # noqa
    PHQ9_FINDING_POSITIVE_SCREENING_FOR_DEPRESSION = "phq9_finding_positive_screening_for_depression"  # noqa
    PHQ9_SCORE = "phq9_observable_score"
    PHQ9_PROCEDURE_DEPRESSION_SCREENING = "phq9_procedure_depression_screening"  # noqa
    PHQ9_SCALE = "phq9_scale"  # https://snomedbrowser.com/Codes/Details/758711000000105  # noqa

    # PHQ-15
    PHQ15_SCORE = "phq15_observable_score"
    PHQ15_PROCEDURE = "phq15_procedure_assessment"
    PHQ15_SCALE = "phq15_scale"

    # PIIOS or "parent infant scale": none

    # PSWQ
    PSWQ_SCALE = "pswq_scale"
    PSWQ_SCORE = "pswq_observable_score"
    PSWQ_PROCEDURE_ASSESSMENT = "pswq_procedure_assessment"

    # QOL-Basic, QOL-SG
    # Unsure, but there is this:
    QOL_SCALE = "qol_scale"
    # ... with no observable/procedure

    # RAND-36: none directly

    # SLUMS: none

    # WEMWBS, SWEMWBS
    WEMWBS_SCALE = "wemwbs_scale"
    WEMWBS_SCORE = "wemwbs_observable_score"
    WEMWBS_PROCEDURE_ASSESSMENT = "wemwbs_procedure_assessment"
    #
    SWEMWBS_SCALE = "swemwbs_scale"
    SWEMWBS_SCORE = "swemwbs_observable_score"
    SWEMWBS_PROCEDURE_ASSESSMENT = "swemwbs_procedure_assessment"

    # WSAS
    WSAS_SCALE = "wsas_scale"
    WSAS_SCORE = "wsas_observable_score"
    WSAS_WORK_SCORE = "wsas_observable_work_score"
    WSAS_RELATIONSHIPS_SCORE = "wsas_observable_relationships_score"
    WSAS_HOME_MANAGEMENT_SCORE = "wsas_observable_home_management_score"
    WSAS_SOCIAL_LEISURE_SCORE = "wsas_observable_social_leisure_score"
    WSAS_PRIVATE_LEISURE_SCORE = "wsas_observable_private_leisure_score"
    WSAS_PROCEDURE_ASSESSMENT = "wsas_procedure_assessment"

    # Y-BOCS, Y-BOCS-SC: none
    # ZBI: none


# =============================================================================
# Perform the lookup
# =============================================================================

VALID_SNOMED_LOOKUPS = set([getattr(SnomedLookup, k) for k in dir(SnomedLookup)
                            if not k.startswith("_")])


def get_snomed_concept(lookup: str, xml_filename: str) -> SnomedConcept:
    """
    Takes a CamCOPS lookup string (see :class:`SnomedLookup`) and returns the
    relevant :class:`SnomedConcept`.

    Args:
        lookup: a CamCOPS SNOMED lookup string
        xml_filename: XML filename to read

    Returns:
        a :class:`SnomedConcept`

    Raises:
        :exc:`KeyError`, if the lookup cannot be found (e.g. UK data not
            installed)

    """
    all_concepts = get_all_snomed_concepts(xml_filename)
    return all_concepts[lookup]


@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def get_all_snomed_concepts(xml_filename: str) -> Dict[str, SnomedConcept]:
    """
    Reads in all SNOMED-CT codes for CamCOPS, from the CamCOPS XML
    representation.

    Args:
        xml_filename: XML filename to read

    Returns:
        dict: maps lookup strings to :class:`SnomedConcept` objects

    """
    log.info("Loading SNOMED-CT XML file: " + xml_filename)
    parser = ElementTree.XMLParser(encoding="UTF-8")
    tree = ElementTree.parse(xml_filename, parser=parser)
    root = tree.getroot()
    identifiers_seen = set()  # type: Set[int]
    all_concepts = {}  # type: Dict[str, SnomedConcept]
    for conceptroot in root.findall("./concept[@lookup]"):
        # Extract info from the XML
        lookup = conceptroot.attrib.get("lookup")
        id_node = conceptroot.find("./id")
        identifier = int(id_node.text)
        name_node = conceptroot.find("./name")
        name = name_node.text or ""
        # Check it
        if lookup not in VALID_SNOMED_LOOKUPS:
            log.debug("Ignoring unknown SNOMED-CT lookup: {!r}".format(lookup))
            continue
        assert identifier not in identifiers_seen, (
            "Duplicate SNOMED-CT identifier: {!r}".format(identifier)
        )
        identifiers_seen.add(identifier)
        # Stash it
        concept = SnomedConcept(identifier, name)
        assert lookup not in all_concepts, (
            "Duplicate SNOMED-CT lookup value: {!r}".format(lookup))
        all_concepts[lookup] = concept
    # Check if any are missing
    missing = sorted(list(VALID_SNOMED_LOOKUPS - set(all_concepts.keys())))
    if missing:
        raise ValueError(
            "The following SNOMED-CT concepts required by CamCOPS are missing "
            "from the XML ({!r}): {!r}".format(xml_filename, missing))
    # Done
    return all_concepts
