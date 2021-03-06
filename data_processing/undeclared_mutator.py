"""
Copyright 2017 Rahul Gupta, Soham Pal, Aditya Kanade, Shirish Shevade.
Indian Institute of Science.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import regex as re

from util.helpers import fix_ids_are_in_program, extract_line_number, get_rev_dict, get_lines, recompose_program


class FailedToMutateException(Exception):
    pass


class CouldNotFindUsesForEitherException(Exception):
    pass


class NothingToMutateException(FailedToMutateException):
    pass


class LoopCountThresholdExceededException(Exception):
    pass


def which_fix_goes_first(program, fix1, fix2):
    try:
        fix1_location = extract_line_number(' '.join(fix1.split()[1:]))
        fix2_location = extract_line_number(' '.join(fix2.split()[1:]))
    except Exception:
        raise

    if not fix_ids_are_in_program(recompose_program(get_lines(program)[fix2_location:]), fix2) and fix_ids_are_in_program(recompose_program(get_lines(program)[fix1_location:]), fix1):
        return fix1

    if not fix_ids_are_in_program(recompose_program(get_lines(program)[fix1_location:]), fix1) and fix_ids_are_in_program(recompose_program(get_lines(program)[fix2_location:]), fix2):
        return fix2

    if not fix_ids_are_in_program(recompose_program(get_lines(program)[fix1_location:]), fix1) and not fix_ids_are_in_program(recompose_program(get_lines(program)[fix2_location:]), fix2):
        raise CouldNotFindUsesForEitherException

    if fix1_location < fix2_location:
        return fix1
    elif fix2_location < fix1_location:
        return fix2

    prog_lines = get_lines(program)
    id_in_fix1 = None
    id_in_fix2 = None

    for token in fix1.split():
        if '_<id>_' in token:
            assert id_in_fix1 is None, fix1
            id_in_fix1 = token
        elif token == '_<op>_[':
            break

    for token in fix2.split():
        if '_<id>_' in token:
            assert id_in_fix2 is None, fix2
            id_in_fix2 = token
        elif token == '_<op>_[':
            break

    assert id_in_fix1 != id_in_fix2, fix1 + ' & ' + fix2
    assert fix1_location == fix2_location

    for i in range(fix1_location, len(prog_lines)):
        for token in prog_lines[i].split():
            if token == id_in_fix1:
                return fix1
            elif token == id_in_fix2:
                return fix2

    assert False, 'unreachable code'


def undeclare_variable(rng, old_program, program_string):
    # Lines
    orig_lines = get_lines(program_string)
    old_lines = get_lines(old_program)

    # Lines to ignore
    struct_lines = []
    structs_deep = 0

    for i, line in enumerate(orig_lines):
        # Should be _<id>_\d+ ???
        if len(re.findall('_<keyword>_struct _<id>_\d@ _<op>_\{', line)) > 0 or \
           len(re.findall('_<keyword>_union _<id>_\d@ _<op>_\{', line)) > 0 or \
           len(re.findall('_<keyword>_enum _<id>_\d@ _<op>_\{', line)) > 0:
            structs_deep += len(re.findall('_<op>_\{', line))
        elif structs_deep > 0:
            structs_deep += len(re.findall('_<op>_\{', line))
            structs_deep -= len(re.findall('_<op>_\}', line))
            assert structs_deep >= 0, str(structs_deep) + " " + line
            struct_lines.append(i)

    global_lines = []
    brackets_deep = 0

    for i, line in enumerate(orig_lines):
        if len(re.findall('_<op>_\{', line)) > 0 or len(re.findall('_<op>_\}', line)) > 0:
            brackets_deep += len(re.findall('_<op>_\{', line))
            brackets_deep -= len(re.findall('_<op>_\}', line))
            assert brackets_deep >= 0, str(brackets_deep) + " " + line
        elif brackets_deep == 0:
            global_lines.append(i)

    # Variables
    variables = []

    for token in program_string.split():
        if '_<id>_' in token:
            if token not in variables:
                variables.append(token)

    # Look for a declaration
    done = False

    rng.shuffle(variables)

    for to_undeclare in variables:

        # Find a location (scope) to undeclare it from
        shuffled_lines = list(set(range(len(orig_lines))) -
                              set(struct_lines + global_lines))
        rng.shuffle(shuffled_lines)

        # NEW
        # Should consider const case and typedef???
        regex_alone_use = '(_<keyword>_(?:struct|enum|union) _<id>_\d+@|_<type>_\w+)((?: _<op>_\*)* %s(?: _<op>_\[(?: [^\]]+)? _<op>_\])*)(?: _<op>_= [^,;]+)(?: _<op>_;)' % to_undeclare
        regex_alone = '((?:_<keyword>_(?:struct|enum|union) _<id>_\d+@|_<type>_\w+)(?: _<op>_\*)* %s(?: _<op>_\[(?: [^\]]+)? _<op>_\])* _<op>_;)' % to_undeclare
        regex_group_leader = '((?:_<keyword>_(?:struct|enum|union) _<id>_\d+@|_<type>_\w+)(?: _<op>_\*)*)( %s(?: _<op>_\[(?: [^\]]+)? _<op>_\])*)(?: _<op>_= [^,;]+)?( _<op>_,)(?:(?: _<op>_\*)* _<id>_\d+@(?: _<op>_\[(?: [^\]]+)? _<op>_\])*(?: _<op>_= [^,;]+)? _<op>_,)*(?:(?: _<op>_\*)* _<id>_\d+@(?: _<op>_\[(?: [^\]]+)? _<op>_\])*(?: _<op>_= [^,;]+)? _<op>_;)' % to_undeclare
        regex_group = '(_<keyword>_(?:struct|enum|union) _<id>_\d+@|_<type>_\w+)(?: _<op>_\*)* _<id>_\d+@(?: _<op>_\[(?: [^\]]+)? _<op>_\])*(?: _<op>_= [^,;]+)?(?: _<op>_,(?: _<op>_\*)* _<id>_\d+@(?: _<op>_\[(?: [^\]]+)? _<op>_\])*(?: _<op>_= [^,;]+)?)*( _<op>_,(?: _<op>_\*)* %s(?: _<op>_\[(?: [^\]]+)? _<op>_\])*(?: _<op>_= [^,;]+)?)(?: _<op>_,(?: _<op>_\*)* _<id>_\d+@(?: _<op>_\[(?: [^\]]+)? _<op>_\])*(?: _<op>_= [^,;]+)?)*(?: _<op>_;)' % to_undeclare

        fix_line = None
        declaration = None
        declaration_pos = None

        # Start our search upwards
        for i in shuffled_lines:
            if len(re.findall(regex_alone_use, orig_lines[i])) == 1:
                m = re.search(regex_alone_use, orig_lines[i])
                declaration = orig_lines[i][m.start(1):m.end(2)] + ' _<op>_;'
                declaration_pos = i

                # Mutate
                orig_lines[i] = orig_lines[i][:m.start(
                    1)] + orig_lines[i][m.end(1) + 1:]
                done = True
                break

            if len(re.findall(regex_alone, orig_lines[i])) == 1:
                m = re.search(regex_alone, orig_lines[i])
                declaration = orig_lines[i][m.start(1):m.end(1)]
                declaration_pos = i

                # Mutate
                orig_lines[i] = orig_lines[i][:m.start(
                    1)] + orig_lines[i][m.end(1) + 1:]
                done = True
                break

            elif len(re.findall(regex_group, orig_lines[i])) == 1:
                m = re.search(regex_group, orig_lines[i])
                declaration = orig_lines[i][m.start(1):m.end(
                    1)] + orig_lines[i][m.start(2):m.end(2)][8:] + ' _<op>_;'
                declaration_pos = i

                try:
                    end_of_declr = declaration.index('_<op>_=')
                    declaration = declaration[:end_of_declr]
                except ValueError:
                    pass

                # Mutate
                orig_lines[i] = orig_lines[i][:m.start(
                    2) + 1] + orig_lines[i][m.end(2) + 1:]
                done = True
                break

            elif len(re.findall(regex_group_leader, orig_lines[i])) == 1:
                m = re.search(regex_group_leader, orig_lines[i])
                declaration = orig_lines[i][m.start(1):m.end(2)] + ' _<op>_;'
                declaration_pos = i

                # Mutate
                orig_lines[i] = orig_lines[i][:m.start(
                    2) + 1] + orig_lines[i][m.end(3) + 1:]
                done = True
                break

    if not done:
        # Failed to find something to undeclare
        raise NothingToMutateException

    # Find the function signature
    fn_regex = '(?:_<keyword>_(?:struct|union|enum) _<id>_\d+@|_<type>_\w+|_<keyword>_void)(?: _<op>_\*)* (?:_<id>_\d+@|_<APIcall>_main) _<op>_\('
    fn_start_regex = '_<op>_\{'
    inserted = False

    assert declaration_pos is not None
    # Why 0 instead of -1???
    for i in range(declaration_pos, 0, -1):
        if len(re.findall(fn_regex, old_lines[i])) == 1:
            for j in range(i, len(old_lines)):
                # Why i instead of j?
                if len(re.findall(fn_start_regex, old_lines[i])) >= 1:
                    fix_line = j
                    break
            inserted = True

        if inserted:
            break
    # ^ May boom: int x = 0; /*eol*/ int y = x;

    if not inserted:
        # print Failed to insert fix
        raise FailedToMutateException
    if fix_line is None:
        # Couldn't find { after function definition
        raise FailedToMutateException

    fix = '_<insertion>_ '

    assert fix_line is not None

    for digit in str(fix_line):
        fix += str(digit) + ' '

    fix += '~ ' + declaration

    if orig_lines[declaration_pos].strip() == '':
        to_delete = declaration_pos
        del orig_lines[to_delete]

    recomposed_program = ''

    for i, line in enumerate(orig_lines):
        for digit in str(i):
            recomposed_program += digit + ' '

        recomposed_program += '~ '
        recomposed_program += line + ' '

    return recomposed_program, fix, fix_line


def id_mutate(rng, prog, max_num_mutations, num_mutated_progs, exact=False, name_dict=None):
    assert max_num_mutations > 0 and num_mutated_progs > 0, "Invalid argument(s) supplied to the function token_mutate"
    corrupted = []
    fixes = []

    for _ in range(num_mutated_progs):
        tokens = prog

        if exact:
            num_mutations = max_num_mutations
        else:
            num_mutations = rng.choice(range(max_num_mutations)) + 1
        mutation_count = 0

        fix_line = None

        for _ in range(num_mutations):
            # Step 2: Induce _[ONE]_ mutation, removing empty lines and shifting program if required
            try:
                mutated, this_fix, _ = undeclare_variable(rng, tokens, tokens)
                mutation_count += 1

            # Couldn't delete anything
            except NothingToMutateException:
                break

            # Insertion or something failed
            except FailedToMutateException:
                raise

            # Deleted something that can't be fixed (all uses gone from the program)
            else:
                # REPLACE! program with mutated version
                tokens = mutated

                if not fix_ids_are_in_program(mutated, this_fix):
                    # Discarding previous fix: all uses are gone
                    continue

                # Update fix line
                if fix_line is not None:
                    fix_line = which_fix_goes_first(
                        mutated, fix_line, this_fix)
                else:
                    fix_line = this_fix

        if fix_line is not None:
            corrupted.append(tokens)
            fixes.append(fix_line)

    for fix in fixes:
        assert fix is not None

    return zip(corrupted, fixes)
