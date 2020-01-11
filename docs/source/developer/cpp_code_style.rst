..  docs/source/developer/cpp_code_style.rst

..  Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).
    .
    This file is part of CamCOPS.
    .
    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    .
    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    .
    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

C++ code style used
===================

.. code-block:: cpp

    /*
        Copyright/license boilerplate
    */


    // In header (.h) files:
    #pragma once

    #define ANY_MASTER_SWITCHES_FOR_FILE
    #define DEBUG_A_SWITCH_THAT_SHOULD_BE_OFF_FOR_RELEASE_MODE

    // In source (.cpp) files:
    #include "myheader.h"

    // Then:
    #include <standard_library_file/in>
    #include <zz_alphabetical/order>
    #include <qt_libraries/in>
    #include <zz_alphabetical/order>
    #include "myproject/libraries/in"
    #include "zz_alphabetical/order"

    #ifdef SOME_MASTER_SWITCH
    #include "conditional/include.h"
    #endif

    #define SOME_MACRO(x) x;  // but... really?

    const QString SOME_CONSTANT;


    namespace mynamespace {

    // ... lower case so it's easy to distinguish Class::member from
    //     namespace::member

    // namespace contents NOT indented

    }  // namespace mynamespace


    class SomeClass {
        // Descriptive comments

        Q_OBJECT  // if applicable

    public:
        // other classes and structs

    public:
        SomeClass();
        // other constructors

        ~SomeClass();

        void someFunction();
        int& rFunctionReturningReference();

        // ...

    protected:
        // functions

    private:
        // functions

    public:
        int public_member;  // e.g. for structs; no "m_"

    private:
        int m_member_variable;  // perfectly clear

        static int s_static_variable;

        // NOT: int mMemberVariable;  // just because Stroustrup and Python habits
        // NOT: int memberVariable;  // helpful to have some indicator of membership
        // NOT: int member_;  // I hate this.

        char* m_pointedto;  // space AFTER the *; see Stroustrup
        char* m_p_pointedto;  // alternative notation; "_p_" for pointer
            // ... not usually necessary.

    };


    // ============================================================================
    // Big divider
    // ============================================================================

    void SomeClass::someFunction(int param)
    {
        // Indents are 4 spaces.

        int stack_variable;
        if (param > 1) {
            braceEvenForSingleStatement();
        }
        if (very_long_condition_1 && very_long_condition_2 &&
                very_long_condition_3 && very_long_condition_4) {
            // we indent the subsequent parts of the "if" statement once more.
        }

        auto someLambdaFunction = [](int param) -> void {
            statements;
        };
    }


    // ----------------------------------------------------------------------------
    // Small divider
    // ----------------------------------------------------------------------------


Note other popular coding standards:

**C++**

- Summary of my preferred style above:

  .. code-block:: none

    SomeClass, someFunction, some_variable, m_some_member_variable
    char* pointer_to_char;

- C++ Super-FAQ: https://isocpp.org/wiki/faq/coding-standards

- Stroustrup, http://www.stroustrup.com/bs_faq2.html#Hungarian

  .. code-block:: none

    some_variable
    const int* pointer;  // http://www.stroustrup.com/bs_faq2.html#whitespace

    some_function  // from the C++ book, anyway

- Qt coding style, https://wiki.qt.io/Qt_Coding_Style

  .. code-block:: none

    SomeClass, someFunction, someVariable, someMemberVariable
    char *pointerToChar;

- Google C++ Style Guide, https://google.github.io/styleguide/cppguide.html#Naming

  .. code-block:: none

    SomeClass, SomeFunction,
    some_stack_variable, some_member_variable_, kSomeConstantVariable

- https://chaste.cs.ox.ac.uk/trac/raw-attachment/wiki/CodingStandardsStrategy/codingStandards.pdf

  .. code-block:: none

    SomeClass, SomeFunction,
    some_stack_variable, mMemberVariable, mpMemberPointer, rReferenceArg,

- Boost, http://www.boost.org/development/requirements.html

  .. code-block:: none

    all_names_like_this

- GCC, https://gcc.gnu.org/codingconventions.html#Cxx_Names

  .. code-block:: none

    m_member
    s_static_member

- http://www.ivanism.com/Articles/CodingStandards.html

  .. code-block:: none

    SomeClass
    SomeNamespace
    SOME_CONSTANT
    SOME_MACRO(x)
    someMemberFunction
    SomeGlobalFunction
    m_someMemberVariable


**Other languages**

- C: Linux kernel style, https://kernel.org/doc/html/latest/process/coding-style.html

  .. code-block:: none

    char *linux_banner;
    char *some_function();

- Python, PEP8, https://www.python.org/dev/peps/pep-0008/

  .. code-block:: none

    SomeClass, some_function,
    some_variable, "_" prefix for "private" members

**Disabling compiler/linter warnings inline**

- For example, compilers disagree on when a ``default:`` label should be
  included in a ``switch`` statement
  (https://github.com/quinoacomputing/quinoa/issues/158).

- For the Visual C++ compiler, an example is:

  .. code-block:: cpp

    #ifdef _MSC_VER  // Compiling under Microsoft Visual C++
    #pragma warning(push)
    #pragma warning(disable: 4100)  // C4100: 'app': unreferenced formal parameter
    #endif

    // problematic code here

    // ... and if we want to resume warnings for this compilation unit:
    #ifdef _MSC_VER  // Compiling under Microsoft Visual C++
    #pragma warning(pop)
    #endif

- For Qt Creator's Clang-Tidy and Clazy, use :menuselection:`Tools --> Options
  --> Analyzer`, copy a starting configuration such as "Clang-Tidy and Clazy
  preselected checks [built-in]", and edit it.
